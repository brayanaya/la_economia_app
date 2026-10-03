import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InventarioComparativaItem(BaseModel):
    """Un renglón de la comparativa de stock por sede (vista de detalle UX)."""
    model_config = ConfigDict(from_attributes=True)

    sede_id: uuid.UUID
    sede_nombre: str
    stock_actual: int
    stock_minimo: int
    precio: Decimal
    ultima_actualizacion: datetime


class InventarioComparativaResponse(BaseModel):
    producto_id: uuid.UUID
    producto_nombre: str
    sedes: list[InventarioComparativaItem]


class InventarioAjusteManual(BaseModel):
    """Ajuste manual de stock por parte de un administrador."""
    stock_actual: int = Field(..., ge=0)
    stock_minimo: int | None = Field(default=None, ge=0)


class SincronizacionProductoItem(BaseModel):
    """Un producto dentro del payload de sincronización de Siigo (RF-05/RF-08)."""
    codigo_barras: str
    stock: int = Field(..., ge=0)
    precio: Decimal = Field(..., ge=0)


class SincronizacionInventarioRequest(BaseModel):
    """
    Cuerpo del endpoint POST /api/v1/middleware/sincronizar-inventario,
    consumido por el middleware que procesa la cola transacciones_siigo.
    """
    evento: str = "actualizacion_inventario"
    codigo_siigo_sede: str
    productos: list[SincronizacionProductoItem]


class ConflictoSincronizacion(BaseModel):
    codigo_barras: str
    motivo: str


class SincronizacionInventarioResponse(BaseModel):
    estado: str
    productos_actualizados: int
    conflictos: list[ConflictoSincronizacion] = []
