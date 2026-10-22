from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.embedding import EmbeddingProducto
from app.models.inventario import InventarioSede
from app.models.producto import Producto
from app.ordenes.models import Orden

router = APIRouter(prefix="/admin", tags=["Administracion"])


class VentasResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_ingresos: Decimal
    ordenes_pagadas: int
    periodo_dias: int


class ProductoStockBajo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    producto_id: uuid.UUID
    producto_nombre: str
    codigo_barras: str
    sede_id: uuid.UUID
    sede_nombre: str
    stock_actual: int
    stock_minimo: int
    stock_reservado: int
    disponible: int


class InventarioEstado(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    productos_bajo_stock: list[ProductoStockBajo]
    total_productos_bajo_stock: int


class MetricasIA(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    busquedas_semanticas: int
    interacciones_agente: int
    embeddings_productos: int
    periodo_dias: int


class EstadisticasAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ventas: VentasResumen
    inventario: InventarioEstado
    ia: MetricasIA


@router.get(
    "/estadisticas",
    response_model=EstadisticasAdmin,
    summary="Estadisticas consolidadas para el panel de administracion",
)
async def obtener_estadisticas(
    periodo_dias: int = 30,
    db: AsyncSession = Depends(get_db),
) -> EstadisticasAdmin:
    """
    Devuelve:
    - Resumen de ventas (ingresos y ordenes en estado PAGADO)
    - Estado del inventario (productos con stock bajo minimo)
    - Metricas de IA (busquedas, interacciones, embeddings)
    """
    desde = datetime.utcnow() - timedelta(days=periodo_dias)

    # 1. Ventas: suma de totales y conteo de ordenes PAGADA en el periodo
    ventas_stmt = (
        select(
            func.coalesce(func.sum(Orden.total), Decimal("0")).label("total_ingresos"),
            func.count(Orden.id).label("ordenes_pagadas"),
        )
        .where(Orden.estado == "PAGADO")
        .where(Orden.creado_en >= desde)
    )
    ventas_result = (await db.execute(ventas_stmt)).one()
    total_ingresos = ventas_result.total_ingresos
    ordenes_pagadas = ventas_result.ordenes_pagadas

    # 2. Inventario: productos con stock_actual <= stock_minimo (bajo stock)
    # Usamos join con InventarioSede, Producto y Sede
    from app.models.sede import Sede

    stock_stmt = (
        select(
            InventarioSede.producto_id,
            Producto.nombre.label("producto_nombre"),
            Producto.codigo_barras,
            InventarioSede.sede_id,
            Sede.nombre.label("sede_nombre"),
            InventarioSede.stock_actual,
            InventarioSede.stock_minimo,
            InventarioSede.stock_reservado,
        )
        .join(Producto, Producto.id == InventarioSede.producto_id)
        .join(Sede, Sede.id == InventarioSede.sede_id)
        .where(InventarioSede.stock_actual <= InventarioSede.stock_minimo)
        .order_by(InventarioSede.stock_actual.asc())
    )
    stock_results = (await db.execute(stock_stmt)).all()

    productos_bajo_stock = [
        ProductoStockBajo(
            producto_id=row.producto_id,
            producto_nombre=row.producto_nombre,
            codigo_barras=row.codigo_barras,
            sede_id=row.sede_id,
            sede_nombre=row.sede_nombre,
            stock_actual=row.stock_actual,
            stock_minimo=row.stock_minimo,
            stock_reservado=row.stock_reservado,
            disponible=row.stock_actual - row.stock_reservado,
        )
        for row in stock_results
    ]

    # 3. Metricas IA
    # Busquedas semanticas: contamos embeddings como proxy de busquedas procesadas
    # (en produccion se guardaria un log de busquedas; aqui usamos embeddings existentes)
    busquedas_stmt = select(func.count(EmbeddingProducto.id)).where(
        EmbeddingProducto.creado_en >= desde
    )
    busquedas_semanticas = (await db.execute(busquedas_stmt)).scalar() or 0

    # Interacciones agente: proxy usando ordenes creadas en el periodo
    # (cada orden pagada implica al menos una interaccion)
    interacciones_stmt = select(func.count(Orden.id)).where(Orden.creado_en >= desde)
    interacciones_agente = (await db.execute(interacciones_stmt)).scalar() or 0

    # Total embeddings de productos
    embeddings_stmt = select(func.count(EmbeddingProducto.id))
    embeddings_productos = (await db.execute(embeddings_stmt)).scalar() or 0

    return EstadisticasAdmin(
        ventas=VentasResumen(
            total_ingresos=total_ingresos,
            ordenes_pagadas=ordenes_pagadas,
            periodo_dias=periodo_dias,
        ),
        inventario=InventarioEstado(
            productos_bajo_stock=productos_bajo_stock,
            total_productos_bajo_stock=len(productos_bajo_stock),
        ),
        ia=MetricasIA(
            busquedas_semanticas=busquedas_semanticas,
            interacciones_agente=interacciones_agente,
            embeddings_productos=embeddings_productos,
            periodo_dias=periodo_dias,
        ),
    )


@router.get(
    "/ordenes-recientes",
    summary="Ultimas ordenes para tabla del dashboard",
)
async def obtener_ordenes_recientes(
    limite: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve las ultimas ordenes con info basica para la tabla del dashboard."""
    from app.ordenes.models import DetalleOrden
    from app.models.sede import Sede

    stmt = (
        select(Orden)
        .options(
            selectinload(Orden.items).selectinload(DetalleOrden.producto_id),
        )
        .order_by(Orden.creado_en.desc())
        .limit(limite)
    )
    ordenes = (await db.execute(stmt)).scalars().all()

    # Cargar nombres de sede
    sede_ids = [o.sede_id for o in ordenes]
    sedes_map = {}
    if sede_ids:
        sedes_stmt = select(Sede).where(Sede.id.in_(sede_ids))
        sedes = (await db.execute(sedes_stmt)).scalars().all()
        sedes_map = {s.id: s.nombre for s in sedes}

    return [
        {
            "id": str(o.id),
            "ticket_id": str(o.ticket_id),
            "sede_id": str(o.sede_id),
            "sede_nombre": sedes_map.get(o.sede_id, "Desconocida"),
            "cliente_nombre": o.cliente_nombre,
            "total": float(o.total),
            "estado": o.estado,
            "creado_en": o.creado_en.isoformat() if o.creado_en else None,
            "items_count": len(o.items),
        }
        for o in ordenes
    ]


from sqlalchemy.orm import selectinload