import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(254), nullable=False, unique=True, index=True)
    nombre = Column(String(120), nullable=False)
    password_hash = Column(String(512), nullable=True)  # nullable for Google OAuth users
    # TOTP / Google Authenticator
    totp_secret = Column(String(32), nullable=True)
    totp_enabled = Column(Boolean, nullable=False, default=False)
    # Google OAuth
    google_sub = Column(String(64), nullable=True, unique=True, index=True)
    google_email = Column(String(254), nullable=True)
    google_nombre = Column(String(120), nullable=True)
    google_avatar_url = Column(String(500), nullable=True)
    # Profile
    telefono = Column(String(30), nullable=True)
    fecha_nacimiento = Column(DateTime(timezone=True), nullable=True)
    # Consent (Ley 1581 Habeas Data)
    consentimiento_datos = Column(Boolean, nullable=False, default=False)
    consentimiento_marketing = Column(Boolean, nullable=False, default=False)
    consentimiento_fecha = Column(DateTime(timezone=True), nullable=True)
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
