from pydantic import BaseModel, Field
import uuid

from app.schemas.busqueda import ProductoRecuperado


class AgenteChatRequest(BaseModel):
    mensaje: str = Field(..., min_length=2, max_length=500)
    sede_id: uuid.UUID | None = Field(
        default=None, description="Si se especifica, filtra disponibilidad por stock en esa sede."
    )


class AgenteChatResponse(BaseModel):
    mensaje: str
    respuesta: str
    productos_recomendados: list[ProductoRecuperado]
    hubo_resultados_relevantes: bool
