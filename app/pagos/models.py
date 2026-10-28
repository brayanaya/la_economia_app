# carrito-v1
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base as Base


class Pago(Base):
    """
    Intento de pago de una orden. Una orden puede tener varios intentos
    (reintentos del cliente); el vigente es el mas reciente por creado_en.

    proveedor: "wompi" (pasarela en linea). Los metodos que no usan pasarela
    ("contra_entrega", "bre_b") no generan filas aqui: quedan en
    ordenes.metodo_pago.
    """

    __tablename__ = "pagos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orden_id = Column(UUID(as_uuid=True), ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False, index=True)
    proveedor = Column(String(30), nullable=False, default="wompi", server_default="wompi")
    estado = Column(String(20), nullable=False, default="pendiente", server_default="pendiente", index=True)
    # Identificador del cobro ante la pasarela; unico porque Wompi lo exige
    # por cobro y es lo que llega de vuelta en eventos y redirect.
    referencia = Column(String(64), nullable=False, unique=True, index=True)
    monto_centavos = Column(Integer, nullable=False)
    moneda = Column(String(3), nullable=False, default="COP", server_default="COP")
    transaccion_id = Column(String(64), nullable=True, index=True)
    # Evento crudo recibido de la pasarela (auditoria y depuracion).
    metadatos = Column(JSON, nullable=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    orden = relationship("Orden", back_populates="pagos")
