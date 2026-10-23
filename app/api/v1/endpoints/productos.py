import math
import re
import unicodedata
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.categoria import Categoria
from app.models.inventario import InventarioSede
from app.models.producto import Producto
from app.models.sede import Sede
from app.schemas.producto import (
    DisponibilidadSede,
    ProductoBusqueda,
    ProductoCreate,
    ProductoListResponse,
    ProductoRead,
)

router = APIRouter(prefix="/productos", tags=["Productos"])


def _normalizar_busqueda(texto: str) -> str:
    sin_tildes = "".join(
        caracter for caracter in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes).strip()


def _texto_normalizado(columna):
    return func.translate(func.lower(func.coalesce(columna, "")), "áéíóúüñ", "aeiouun")


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


@router.get("/buscar", response_model=list[ProductoBusqueda], summary="Buscar por texto de catálogo")
async def buscar_productos(
    q: str = Query(..., min_length=1, max_length=120),
    sede_id: uuid.UUID | None = Query(default=None),
    limite: int = Query(default=40, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ProductoBusqueda]:
    """Busca coincidencias de todos los términos, sin depender de embeddings."""
    consulta = _normalizar_busqueda(q)
    terminos = consulta.split()
    if not terminos:
        return []

    campos = [
        _texto_normalizado(Producto.nombre),
        _texto_normalizado(Producto.descripcion),
        _texto_normalizado(Categoria.nombre),
        _texto_normalizado(Producto.codigo_barras),
    ]
    stmt = select(Producto, Categoria.nombre.label("categoria"))
    stmt = stmt.outerjoin(Categoria, Categoria.id == Producto.categoria_id)

    if sede_id is not None:
        stmt = stmt.outerjoin(
            InventarioSede,
            and_(InventarioSede.producto_id == Producto.id, InventarioSede.sede_id == sede_id),
        ).add_columns(func.coalesce(InventarioSede.stock_actual, 0).label("stock"))
    else:
        stock_por_producto = (
            select(
                InventarioSede.producto_id.label("producto_id"),
                func.coalesce(func.sum(InventarioSede.stock_actual), 0).label("stock"),
            )
            .group_by(InventarioSede.producto_id)
            .subquery()
        )
        stmt = stmt.outerjoin(stock_por_producto, stock_por_producto.c.producto_id == Producto.id)
        stmt = stmt.add_columns(func.coalesce(stock_por_producto.c.stock, 0).label("stock"))

    for termino in terminos:
        patron = f"%{termino}%"
        stmt = stmt.where(or_(*(campo.ilike(patron, escape="\\") for campo in campos)))

    nombre = _texto_normalizado(Producto.nombre)
    stmt = stmt.order_by(
        case(
            (nombre == consulta, 0),
            (nombre.ilike(f"%{consulta}%", escape="\\"), 1),
            else_=2,
        ),
        Producto.nombre,
    ).limit(limite)

    filas = (await db.execute(stmt)).all()
    return [
        ProductoBusqueda(
            id=fila[0].id,
            nombre=fila[0].nombre,
            precio=fila[0].precio_venta,
            stock=fila.stock,
            categoria=fila.categoria,
            imagen=fila[0].imagen_url,
        )
        for fila in filas
    ]


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
