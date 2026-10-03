import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class BusquedaSemanticaRequest(BaseModel):
    """
    Cuerpo de la solicitud de búsqueda semántica, utilizada tanto por el
    agente de IA (retriever del pipeline RAG) como, potencialmente, por un
    buscador enriquecido en el catálogo del cliente.
    """
    consulta: str = Field(..., min_length=2, max_length=500)
    sede_id: uuid.UUID | None = Field(
        default=None, description="Si se especifica, aplica el filtro híbrido de stock > 0 en esa sede."
    )
    top_k: int = Field(default=8, ge=1, le=20)
    limite_resultados: int = Field(default=4, ge=1, le=10)


class ProductoRecuperado(BaseModel):
    producto_id: uuid.UUID
    nombre: str
    categoria_nombre: str | None = None
    precio: Decimal | None = None
    stock_sede: int | None = None
    similitud: float


class BusquedaSemanticaResponse(BaseModel):
    consulta: str
    resultados: list[ProductoRecuperado]
    candidatos_ampliados: bool = Field(
        default=False,
        description="True si se activó el fallback k=16 por escasez de candidatos disponibles (numeral 10.3).",
    )
