# carrito-v1
import uuid
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db as get_db
from app.auth.router import current_session, check_csrf
from app.auth.models import CustomerSession
from app.core.catalog_state import catalogo_state, get_catalogo_state
from app.services.providers import get_proveedor_catalogo
from app.services.providers.base import ProductProvider, ProductoNoEncontradoError
from .crud import obtener_orden
from .models import DetalleOrden, Orden
from .schemas import OrdenConsultaOut, OrdenCreate, OrdenOut

router = APIRouter(prefix="/ordenes", tags=["ordenes"])
CENTAVOS = Decimal("0.01")


async def _revalidar_items_pedido(
    proveedor: ProductProvider,
    items: list,
    sede_id: str
) -> tuple[list, list]:
    """
    Revalida items del pedido contra el catálogo autoritativo.
    Retorna (items_validados, errores) donde items_validados tiene precio_unitario actualizado.

    Usa el contrato ProductProvider correctamente:
    - obtener_por_id: verifica que el producto existe
    - obtener_precio: obtiene precio autoritativo por sede
    - verificar_stock: verifica disponibilidad real por sede
    """
    items_validados = []
    errores = []

    for it in items:
        try:
            # 1. Verificar que el producto existe en catálogo
            producto = await proveedor.obtener_por_id(it.producto_id)
            if not producto:
                errores.append(f"Producto {it.producto_id} ({it.nombre}) no encontrado en catálogo")
                continue

            # 2. Verificar stock real en la sede
            stock_info = await proveedor.verificar_stock(it.producto_id, sede_id)
            if stock_info.cantidad < it.cantidad:
                errores.append(
                    f"Stock insuficiente para {producto.nombre} en sede {sede_id}: "
                    f"solicitado {it.cantidad}, disponible {stock_info.cantidad}"
                )
                continue

            if not stock_info.disponible:
                errores.append(f"Producto {producto.nombre} no disponible en sede {sede_id}")
                continue

            # 3. Obtener precio autoritativo para la sede
            precio_info = await proveedor.obtener_precio(it.producto_id, sede_id=sede_id)
            precio_autoritario = Decimal(str(precio_info.precio_final))
            if precio_autoritario <= 0:
                errores.append(f"Producto {producto.nombre} sin precio válido en sede {sede_id}")
                continue

            items_validados.append({
                "producto_id": it.producto_id,
                "nombre": producto.nombre,  # Usar nombre del catálogo (autoridad)
                "cantidad": it.cantidad,
                "precio_unitario": precio_autoritario,
                "imagen_url": getattr(producto, 'imagen_url', None) or it.imagen_url,
            })

        except ProductoNoEncontradoError:
            errores.append(f"Producto {it.producto_id} ({it.nombre}) no encontrado en catálogo")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error revalidando {it.producto_id}: {e}")
            errores.append(f"Error validando {it.producto_id} ({it.nombre})")

    return items_validados, errores


@router.post("/", response_model=OrdenOut, status_code=status.HTTP_201_CREATED)
async def crear_orden(
    payload: OrdenCreate,
    request: Request,
    session: CustomerSession = Depends(current_session),
    db: AsyncSession = Depends(get_db),
    proveedor: ProductProvider = Depends(get_proveedor_catalogo),
):
    check_csrf(request, session)

    # Verificar estado del catálogo - en producción falla si no está conectado
    if not catalogo_state.esta_conectado:
        import logging
        logging.getLogger(__name__).error("Intento de crear orden sin catálogo conectado")
        raise HTTPException(
            status_code=503,
            detail="Catálogo no disponible. No se pueden crear órdenes sin precios autoritativos."
        )

    # Revalidar items contra catálogo autoritativo (fix issue #4 - integridad comercial)
    sede_id_str = str(payload.sede_id)
    items_validados, errores = await _revalidar_items_pedido(proveedor, payload.items, sede_id_str)

    if errores:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "No se pudo crear la orden: validación de catálogo fallida",
                "errores": errores,
            }
        )

    if not items_validados:
        raise HTTPException(status_code=400, detail="Ningún item válido para la orden")

    # Calcular total con precios revalidados
    orden_id = uuid.uuid4()
    total = Decimal("0")
    detalles = []
    for it in items_validados:
        subtotal = (it["precio_unitario"] * it["cantidad"]).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
        total += subtotal
        detalles.append(
            DetalleOrden(
                id=uuid.uuid4(),
                orden_id=orden_id,
                producto_id=it["producto_id"],
                nombre=it["nombre"],
                imagen_url=it["imagen_url"],
                cantidad=it["cantidad"],
                precio_unitario=it["precio_unitario"],
                subtotal=subtotal,
            )
        )

    orden = Orden(
        id=orden_id,
        sede_id=payload.sede_id,
        customer_id=session.user_id,
        cliente_nombre=payload.cliente_nombre,
        cliente_telefono=payload.cliente_telefono,
        notas=payload.notas,
        metodo_pago=payload.metodo_pago,
        total=total,
        estado="pendiente",
        items=detalles,
    )
    db.add(orden)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Sede inválida o datos inconsistentes")

    resultado = await db.execute(
        select(Orden)
        .options(selectinload(Orden.items))
        .where(Orden.id == orden_id)
        .execution_options(populate_existing=True)
    )
    return resultado.scalar_one()


@router.get("/{orden_id}", response_model=OrdenConsultaOut)
async def consultar_orden(orden_id: uuid.UUID, response: Response, db: AsyncSession = Depends(get_db)):
    orden = await obtener_orden(db, orden_id)
    if orden is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    response.headers["Cache-Control"] = "no-store"
    return orden
