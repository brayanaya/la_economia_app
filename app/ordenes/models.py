# carrito-v1
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base as Base


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sede_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    cliente_nombre = Column(String(120), nullable=False)
    cliente_telefono = Column(String(30), nullable=True)
    notas = Column(String(500), nullable=True)
    total = Column(Numeric(12, 2), nullable=False)
    estado = Column(String(20), nullable=False, default="pendiente", server_default="pendiente")
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    items = relationship(
        "DetalleOrden",
        back_populates="orden",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DetalleOrden(Base):
    __tablename__ = "detalles_orden"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orden_id = Column(UUID(as_uuid=True), ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(String(64), nullable=False)
    nombre = Column(String(200), nullable=False)
    imagen_url = Column(String(500), nullable=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)

    orden = relationship("Orden", back_populates="items")
