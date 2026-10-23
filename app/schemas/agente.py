import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.busqueda import ProductoRecuperado


class MensajeHistorial(BaseModel):
    rol: Literal["usuario", "asistente"]
    texto: str = Field(..., min_length=1, max_length=1000)


class AgenteChatRequest(BaseModel):
    mensaje: str = Field(..., min_length=2, max_length=500)
    sede_id: uuid.UUID | None = Field(
        default=None, description="Si se especifica, filtra disponibilidad por stock en esa sede."
    )
    historial: list[MensajeHistorial] = Field(default_factory=list, max_length=8)


class AgenteChatResponse(BaseModel):
    mensaje: str
    respuesta: str
    productos_recomendados: list[ProductoRecuperado]
    hubo_resultados_relevantes: bool
