import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.inventario import InventarioSede
from app.models.producto import Producto
from app.models.sede import Sede
from app.models.transaccion_siigo import EstadoTransaccionSiigo, TransaccionSiigo
from app.schemas.inventario import (
    ConflictoSincronizacion,
    InventarioAjusteManual,
    InventarioComparativaItem,
    InventarioComparativaResponse,
    SincronizacionInventarioRequest,
    SincronizacionInventarioResponse,
)

router = APIRouter(tags=["Inventario"])


@router.get(
    "/inventario/{producto_id}",
    response_model=InventarioComparativaResponse,
    summary="Comparativa de stock por sede (RF-06 / vista de detalle UX)",
)
async def comparativa_stock_por_sede(
    producto_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> InventarioComparativaResponse:
    producto = await db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    stmt = (
        select(InventarioSede)
        .where(InventarioSede.producto_id == producto_id)
        .options(selectinload(InventarioSede.sede))
    )
    inventarios = (await db.execute(stmt)).scalars().all()

    sedes = [
        InventarioComparativaItem(
            sede_id=inv.sede_id,
            sede_nombre=inv.sede.nombre,
            stock_actual=inv.stock_actual,
            stock_minimo=inv.stock_minimo,
            precio=producto.precio_venta,
            ultima_actualizacion=inv.ultima_actualizacion,
        )
        for inv in inventarios
    ]

    return InventarioComparativaResponse(
        producto_id=producto.id, producto_nombre=producto.nombre, sedes=sedes
    )


@router.patch(
    "/inventario/{inventario_id}/ajuste-manual",
    response_model=InventarioComparativaItem,
    summary="Ajuste manual de stock por un administrador",
)
async def ajustar_stock_manual(
    inventario_id: uuid.UUID,
    payload: InventarioAjusteManual,
    db: AsyncSession = Depends(get_db),
) -> InventarioComparativaItem:
    inventario = await db.get(
        InventarioSede, inventario_id, options=[selectinload(InventarioSede.sede)]
    )
    if inventario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de inventario no encontrado")

    inventario.stock_actual = payload.stock_actual
    if payload.stock_minimo is not None:
        inventario.stock_minimo = payload.stock_minimo

    await db.commit()
    await db.refresh(inventario, attribute_names=["sede", "producto"])

    return InventarioComparativaItem(
        sede_id=inventario.sede_id,
        sede_nombre=inventario.sede.nombre,
        stock_actual=inventario.stock_actual,
        stock_minimo=inventario.stock_minimo,
        precio=inventario.producto.precio_venta,
        ultima_actualizacion=inventario.ultima_actualizacion,
    )


@router.post(
    "/middleware/sincronizar-inventario",
    response_model=SincronizacionInventarioResponse,
    summary="Webhook/polling de sincronización con Siigo (RF-05, RF-08)",
)
async def sincronizar_inventario(
    payload: SincronizacionInventarioRequest, db: AsyncSession = Depends(get_db)
) -> SincronizacionInventarioResponse:
    """
    Punto de entrada del middleware descrito en el Flujo B del documento
    de arquitectura. Este endpoint es interno (no expuesto al cliente
    final) y debe protegerse en producción mediante un token de servicio
    de alcance restringido (scope: middleware:write), conforme al
    requerimiento RNF-04.
    """
    # 1. Registrar el evento crudo en la cola de auditoría/reintentos,
    #    ANTES de intentar procesarlo, para no perder información ante
    #    un fallo a mitad de la sincronización (patrón outbox simplificado).
    sede_stmt = select(Sede).where(Sede.nombre == payload.codigo_siigo_sede)
    # NOTA: en producción, la correspondencia sede <-> código Siigo debe
    # resolverse mediante una columna dedicada (p. ej. sedes.codigo_siigo);
    # aquí se resuelve por nombre como simplificación de esta primera fase.
    sede = (await db.execute(sede_stmt)).scalar_one_or_none()

    transaccion = TransaccionSiigo(
        sede_id=sede.id if sede else None,
        payload_json=payload.model_dump(mode="json"),
        estado=EstadoTransaccionSiigo.PENDIENTE.value,
    )
    if sede is None:
        transaccion.estado = EstadoTransaccionSiigo.ERROR.value
        transaccion.error_log = f"Sede no reconocida: {payload.codigo_siigo_sede}"
        db.add(transaccion)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sede no reconocida para código Siigo: {payload.codigo_siigo_sede}",
        )

    db.add(transaccion)
    await db.flush()  # asigna transaccion.id sin cerrar la transacción SQL

    # 2. Procesar cada producto del payload contra el catálogo unificado.
    productos_actualizados = 0
    conflictos: list[ConflictoSincronizacion] = []

    for item in payload.productos:
        producto_stmt = select(Producto).where(Producto.codigo_barras == item.codigo_barras)
        producto = (await db.execute(producto_stmt)).scalar_one_or_none()

        if producto is None:
            conflictos.append(
                ConflictoSincronizacion(
                    codigo_barras=item.codigo_barras,
                    motivo="producto_no_encontrado_en_catalogo_unificado",
                )
            )
            continue

        inv_stmt = select(InventarioSede).where(
            InventarioSede.producto_id == producto.id,
            InventarioSede.sede_id == sede.id,
        )
        inventario = (await db.execute(inv_stmt)).scalar_one_or_none()

        if inventario is None:
            # Alta automática del registro de inventario si el producto
            # nunca se había vendido antes en esta sede.
            inventario = InventarioSede(
                producto_id=producto.id, sede_id=sede.id, stock_actual=0, stock_minimo=0
            )
            db.add(inventario)

        inventario.stock_actual = item.stock
        producto.precio_venta = item.precio  # el precio es global al producto en este esquema
        productos_actualizados += 1

    # 3. Cerrar el ciclo de vida de la transacción de sincronización.
    transaccion.procesado_en = datetime.now(timezone.utc)
    transaccion.estado = (
        EstadoTransaccionSiigo.PROCESADO.value
        if not conflictos
        else EstadoTransaccionSiigo.ERROR.value
    )
    if conflictos:
        transaccion.error_log = "; ".join(c.motivo for c in conflictos)
        transaccion.intentos += 1

    await db.commit()

    return SincronizacionInventarioResponse(
        estado="sincronizado" if not conflictos else "sincronizado_con_conflictos",
        productos_actualizados=productos_actualizados,
        conflictos=conflictos,
    )
