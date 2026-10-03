import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base


class EmbeddingProducto(Base):
    __tablename__ = "embeddings_productos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("productos.id", ondelete="CASCADE"), nullable=False
    )
    contenido_textual: Mapped[str] = mapped_column(Text, nullable=False)
    # Dimensión fija en 768 para ser compatible tanto con modelos de
    # Sentence-Transformers multilingües como con OpenAI text-embedding-3-small
    # invocado con el parámetro dimensions=768 (ver app/services/embeddings.py).
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimensions))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    producto: Mapped["Producto"] = relationship(back_populates="embeddings")

    def __repr__(self) -> str:
        return f"<EmbeddingProducto producto={self.producto_id}>"
