import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EstadoTransaccionSiigo(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PROCESADO = "PROCESADO"
    ERROR = "ERROR"


class TransaccionSiigo(Base):
    """
    Cola de sincronización consumida por el middleware de integración con
    Siigo (ver documento de arquitectura, Flujo B). Cada fila representa
    un evento de actualización de inventario/facturación pendiente de
    propagar hacia el catálogo unificado.
    """
    __tablename__ = "transacciones_siigo"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    sede_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False
    )
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EstadoTransaccionSiigo.PENDIENTE.value
    )
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_log: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sede: Mapped["Sede"] = relationship()

    def __repr__(self) -> str:
        return f"<TransaccionSiigo {self.id} estado={self.estado}>"
