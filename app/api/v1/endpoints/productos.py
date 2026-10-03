import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.categoria import Categoria
from app.models.inventario import InventarioSede
from app.models.producto import Producto
from app.models.sede import Sede
from app.schemas.producto import (
    DisponibilidadSede,
    ProductoCreate,
    ProductoListResponse,
    ProductoRead,
)

router = APIRouter(prefix="/productos", tags=["Productos"])


def _to_producto_read(producto: Producto) -> ProductoRead:
    # Nota de esquema: en este modelo el precio es único por producto
    # (columna productos.precio_venta) y NO varía por sede; solo el stock
    # es propio de cada sede (tabla inventario_sedes). Si en una fase
    # posterior el negocio requiere precios diferenciados por sede, el
    # campo `precio` debería trasladarse a inventario_sedes.
    disponibilidad = [
        DisponibilidadSede(
            sede_id=inv.sede_id,
            sede_nombre=inv.sede.nombre,
            stock_actual=inv.stock_actual,
            precio=producto.precio_venta,
        )
        for inv in producto.inventarios
    ]
    return ProductoRead(
        id=producto.id,
        codigo_barras=producto.codigo_barras,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        categoria_id=producto.categoria_id,
        categoria_nombre=producto.categoria.nombre if producto.categoria else None,
        precio_venta=producto.precio_venta,
        es_saludable=producto.es_saludable,
        imagen_url=producto.imagen_url,
        disponibilidad=disponibilidad,
    )


@router.get("", response_model=ProductoListResponse, summary="Listar catálogo (RF-01)")
async def listar_productos(
    sede_id: uuid.UUID | None = Query(default=None, description="Filtra disponibilidad por sede"),
    categoria_id: uuid.UUID | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    limite: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ProductoListResponse:
    """
    Retorna el catálogo unificado, filtrable por sede y categoría, con
    paginación. Contrato equivalente al especificado para
    GET /api/v1/productos en el documento de arquitectura.
    """
    stmt = (
        select(Producto)
        .options(
            selectinload(Producto.categoria),
            selectinload(Producto.inventarios).selectinload(InventarioSede.sede),
        )
    )

    if categoria_id is not None:
        stmt = stmt.where(Producto.categoria_id == categoria_id)

    if sede_id is not None:
        # Solo productos que tengan un registro de inventario en la sede dada
        stmt = stmt.where(
            Producto.id.in_(
                select(InventarioSede.producto_id).where(InventarioSede.sede_id == sede_id)
            )
        )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_registros = (await db.execute(total_stmt)).scalar_one()

    stmt = stmt.order_by(Producto.nombre).offset((pagina - 1) * limite).limit(limite)
    productos = (await db.execute(stmt)).scalars().unique().all()

    total_paginas = max(1, math.ceil(total_registros / limite))

    return ProductoListResponse(
        datos=[_to_producto_read(p) for p in productos],
        pagina=pagina,
        limite=limite,
        total_registros=total_registros,
        total_paginas=total_paginas,
    )


@router.get("/{producto_id}", response_model=ProductoRead, summary="Detalle de producto")
async def obtener_producto(
    producto_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> ProductoRead:
    stmt = (
        select(Producto)
        .where(Producto.id == producto_id)
        .options(
            selectinload(Producto.categoria),
            selectinload(Producto.inventarios).selectinload(InventarioSede.sede),
        )
    )
    producto = (await db.execute(stmt)).scalar_one_or_none()
    if producto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return _to_producto_read(producto)


@router.post(
    "",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear producto (RF-09, rol administrador)",
)
async def crear_producto(
    payload: ProductoCreate, db: AsyncSession = Depends(get_db)
) -> ProductoRead:
    categoria = await db.get(Categoria, payload.categoria_id)
    if categoria is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoría inexistente")

    existente = await db.execute(
        select(Producto).where(Producto.codigo_barras == payload.codigo_barras)
    )
    if existente.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un producto con ese código de barras",
        )

    producto = Producto(**payload.model_dump())
    db.add(producto)
    await db.commit()
    await db.refresh(producto, attribute_names=["categoria", "inventarios"])

    return _to_producto_read(producto)
