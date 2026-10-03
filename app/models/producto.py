import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    codigo_barras: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    categoria_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False
    )
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    es_saludable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    imagen_url: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    categoria: Mapped["Categoria"] = relationship(back_populates="productos")
    inventarios: Mapped[list["InventarioSede"]] = relationship(
        back_populates="producto", cascade="all, delete-orphan"
    )
    embeddings: Mapped[list["EmbeddingProducto"]] = relationship(
        back_populates="producto", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Producto {self.nombre} ({self.codigo_barras})>"
