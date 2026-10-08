"""
Este módulo importa todos los modelos ORM en un único punto, de manera
que Base.metadata los registre correctamente y Alembic pueda detectarlos
durante `alembic revision --autogenerate`.
"""
from app.models.categoria import Categoria  # noqa: F401
from app.models.consentimiento import ConsentimientoHabeasData  # noqa: F401
from app.models.embedding import EmbeddingProducto  # noqa: F401
from app.models.inventario import InventarioSede  # noqa: F401
from app.models.producto import Producto  # noqa: F401
from app.models.sede import Sede  # noqa: F401
from app.models.transaccion_siigo import TransaccionSiigo  # noqa: F401

__all__ = [
    "Categoria",
    "ConsentimientoHabeasData",
    "EmbeddingProducto",
    "InventarioSede",
    "Producto",
    "Sede",
    "TransaccionSiigo",
]
