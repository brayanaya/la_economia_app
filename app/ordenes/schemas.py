# carrito-v1
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MetodoPago = Literal["contra_entrega", "bre_b", "wompi"]


class ItemOrdenIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    producto_id: str = Field(min_length=1, max_length=64)
    nombre: str = Field(min_length=1, max_length=200)
    cantidad: int = Field(ge=1, le=99)
    precio_unitario: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    imagen_url: Optional[str] = Field(default=None, max_length=500)


class OrdenCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sede_id: UUID
    cliente_nombre: str = Field(min_length=2, max_length=120)
    cliente_telefono: Optional[str] = Field(default=None, max_length=30)
    notas: Optional[str] = Field(default=None, max_length=500)
    metodo_pago: MetodoPago = "contra_entrega"
    items: List[ItemOrdenIn] = Field(min_length=1, max_length=100)


class DetalleOrdenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    producto_id: str
    nombre: str
    imagen_url: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class OrdenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sede_id: UUID
    cliente_nombre: str
    cliente_telefono: Optional[str] = None
    notas: Optional[str] = None
    total: Decimal
    metodo_pago: Optional[str] = None
    estado: str
    creado_en: datetime
    items: List[DetalleOrdenOut]


class DetalleOrdenPublicoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str
    imagen_url: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class OrdenConsultaOut(BaseModel):
    """Vista publica de un pedido: sin telefono ni notas (datos personales, Ley 1581 de 2012)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sede_id: UUID
    cliente_nombre: str
    total: Decimal
    metodo_pago: Optional[str] = None
    estado: str
    creado_en: datetime
    items: List[DetalleOrdenPublicoOut]
