import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SedeBase(BaseModel):
    nombre: str
    direccion: str | None = None


class SedeCreate(SedeBase):
    pass


class SedeRead(SedeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    creado_en: datetime
