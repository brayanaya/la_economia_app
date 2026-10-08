import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConsentimientoCreate(BaseModel):
    acepto_politica: bool
    acepto_cookies: bool
    version_politica: str = Field(..., min_length=1, max_length=32)


class ConsentimientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    acepto_politica: bool
    acepto_cookies: bool
    version_politica: str
    fecha_registro: datetime
    mensaje: str = "Autorizacion registrada para fines de auditoria."