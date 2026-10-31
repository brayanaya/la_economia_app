from pydantic import BaseModel, Field
from typing import Optional, Any
import uuid


class AgenteChatRequest(BaseModel):
    mensaje: str = Field(..., min_length=2, max_length=500)
    sede_id: uuid.UUID | None = Field(
        default=None, description="Si se especifica, filtra disponibilidad por stock en esa sede."
    )


class RecetaIngredienteResponse(BaseModel):
    nombre: str
    cantidad: str
    busqueda_catalogo: str
    obligatorio: bool
    notas: str = ""


class RecetaResponse(BaseModel):
    id: str
    nombre: str
    descripcion: str
    categoria: str
    tiempo_min: int
    porciones: int
    costo_estimado_cop: float
    imagen_url: Optional[str] = None
    ingredientes: list[RecetaIngredienteResponse]
    pasos: list[str]
    tags: list[str]


class AgenteChatResponse(BaseModel):
    mensaje: str
    respuesta: str
    productos_recomendados: list[Any]
    hubo_resultados_relevantes: bool
    receta: Optional[RecetaResponse] = None