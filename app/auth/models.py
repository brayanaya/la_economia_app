import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(254), nullable=False, unique=True, index=True)
    nombre = Column(String(120), nullable=False)
    password_hash = Column(String(512), nullable=False)
    sessions = relationship("CustomerSession", cascade="all, delete-orphan", back_populates="user")

class CustomerSession(Base):
    __tablename__ = "customer_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    csrf_token = Column(String(64), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user = relationship("Customer", back_populates="sessions")
