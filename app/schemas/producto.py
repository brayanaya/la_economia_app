import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DisponibilidadSede(BaseModel):
    """Disponibilidad de un producto en una sede específica (RF-06)."""
    model_config = ConfigDict(from_attributes=True)

    sede_id: uuid.UUID
    sede_nombre: str
    stock_actual: int
    precio: Decimal


class ProductoBase(BaseModel):
    codigo_barras: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=200)
    descripcion: str | None = None
    categoria_id: uuid.UUID
    precio_venta: Decimal = Field(..., ge=0)
    es_saludable: bool = False
    imagen_url: str | None = None


class ProductoCreate(ProductoBase):
    """Payload para RF-09 (gestión administrativa del catálogo)."""
    pass


class ProductoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    categoria_id: uuid.UUID | None = None
    precio_venta: Decimal | None = Field(default=None, ge=0)
    es_saludable: bool | None = None
    imagen_url: str | None = None


class ProductoRead(ProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    categoria_nombre: str | None = None
    disponibilidad: list[DisponibilidadSede] = []


class ProductoListResponse(BaseModel):
    """Envoltorio de paginación para GET /api/v1/productos (RF-01)."""
    datos: list[ProductoRead]
    pagina: int
    limite: int
    total_registros: int
    total_paginas: int
