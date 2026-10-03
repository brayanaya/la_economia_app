import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InventarioSede(Base):
    __tablename__ = "inventario_sedes"
    __table_args__ = (
        UniqueConstraint("producto_id", "sede_id", name="uq_producto_sede"),
        CheckConstraint("stock_actual >= 0", name="ck_stock_actual_no_negativo"),
        CheckConstraint("stock_minimo >= 0", name="ck_stock_minimo_no_negativo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("productos.id", ondelete="CASCADE"), nullable=False
    )
    sede_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sedes.id", ondelete="CASCADE"), nullable=False
    )
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultima_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    producto: Mapped["Producto"] = relationship(back_populates="inventarios")
    sede: Mapped["Sede"] = relationship(back_populates="inventarios")

    def __repr__(self) -> str:
        return f"<InventarioSede producto={self.producto_id} sede={self.sede_id} stock={self.stock_actual}>"
