import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConsentimientoHabeasData(Base):
    """Registro de auditoria de autorizaciones de tratamiento de datos y cookies (Ley 1581)."""

    __tablename__ = "consentimientos_habeas_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    ip_origen: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512))
    acepto_politica: Mapped[bool] = mapped_column(Boolean, nullable=False)
    acepto_cookies: Mapped[bool] = mapped_column(Boolean, nullable=False)
    version_politica: Mapped[str] = mapped_column(String(32), nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )