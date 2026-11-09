"""
Modelos SQLAlchemy para Conversación y Mensajes con PostgreSQL + pgvector.
"""
import enum
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TipoRemitente(str, enum.Enum):
    """Tipo de remitente del mensaje."""
    USUARIO = "usuario"
    ASISTENTE = "asistente"
    SISTEMA = "sistema"


class Conversacion(Base):
    """
    Tabla principal de conversaciones.

    Una conversación pertenece a un usuario y contiene múltiples mensajes.
    Incluye campos para contexto persistente (productos_recientes, receta_actual, etc.)
    y un resumen automático para conversaciones largas.
    """
    __tablename__ = "conversaciones"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Contexto persistente para el agente
    productos_recientes: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    receta_actual: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    lista_mercado: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    presupuesto: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Resumen automático para conversaciones largas
    resumen: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Metadatos
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    # Relaciones
    mensajes: Mapped[list["Mensaje"]] = relationship(
        "Mensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="Mensaje.creado_en"
    )

    # Índices
    __table_args__ = (
        Index("ix_conversaciones_usuario_actualizado", "usuario_id", "actualizado_en"),
    )

    def __repr__(self) -> str:
        return f"<Conversacion(id={self.id}, usuario_id={self.usuario_id}, mensajes={len(self.mensajes)})>"


class Mensaje(Base):
    """
    Tabla de mensajes individuales dentro de una conversación.

    Cada mensaje tiene un embedding vectorial para búsqueda semántica
    y metadatos de tokens para control de costos.
    """
    __tablename__ = "mensajes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    conversacion_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversaciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Contenido del mensaje
    remitente: Mapped[TipoRemitente] = mapped_column(
        Enum(TipoRemitente, name="tipo_remitente_enum", values_callable=lambda x: [e.value for e in x], create_type=True),
        nullable=False
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    # Embedding para búsqueda semántica (dim=768 para nomic-embed-text o similar)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(768), nullable=True)
    # Metadatos de tokens (para control de costos y contexto)
    tokens_entrada: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_salida: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    modelo_usado: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Metadatos temporales
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    # Relaciones
    conversacion: Mapped["Conversacion"] = relationship("Conversacion", back_populates="mensajes")

    # Índices
    __table_args__ = (
        Index("ix_mensajes_conversacion_creado", "conversacion_id", "creado_en"),
        # Índice para búsqueda vectorial (se crea con pgvector)
        # Index("ix_mensajes_embedding", "embedding", postgresql_using="ivfflat", postgresql_with={"lists": 100}),
    )

    def __repr__(self) -> str:
        return f"<Mensaje(id={self.id}, conversacion_id={self.conversacion_id}, remitente={self.remitente.value})>"