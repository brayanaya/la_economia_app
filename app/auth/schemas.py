from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)
    nombre: str = Field(min_length=2, max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=30)
    consentimiento_datos: bool = True
    consentimiento_marketing: bool = False
    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold()


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    totp_code: Optional[str] = Field(default=None, pattern=r"^\d{6}$")
    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold()


class GoogleAuthIn(BaseModel):
    """Google OAuth token from frontend (ID token)."""
    id_token: str = Field(min_length=100)
    model_config = ConfigDict(str_strip_whitespace=True)


class MagicLinkIn(BaseModel):
    """Request a magic link for passwordless login."""
    email: EmailStr
    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold()


class MagicLinkVerifyIn(BaseModel):
    """Verify magic link token."""
    token: str = Field(min_length=32)
    model_config = ConfigDict(str_strip_whitespace=True)


# TOTP / Google Authenticator
class TotpSetupOut(BaseModel):
    """TOTP setup data for QR code."""
    secret: str
    uri: str
    qr_code_url: str


class TotpVerifyIn(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class TotpStatusOut(BaseModel):
    enabled: bool


# User profile
class UserOut(BaseModel):
    id: str
    email: str
    nombre: str
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[datetime] = None
    totp_enabled: bool = False
    google_linked: bool = False
    consentimiento_datos: bool = False
    consentimiento_marketing: bool = False


class UserUpdateIn(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=30)
    consentimiento_datos: Optional[bool] = None
    consentimiento_marketing: Optional[bool] = None
    model_config = ConfigDict(str_strip_whitespace=True)


class AuthOut(BaseModel):
    user: UserOut
    csrf_token: str
    requires_totp: bool = False  # True if user has TOTP enabled and needs to provide code


class ConsentOut(BaseModel):
    """Consent information for Ley 1581 compliance."""
    consentimiento_datos: bool
    consentimiento_marketing: bool
    consentimiento_fecha: Optional[datetime] = None
    version: str = "1.0"
    politica_url: str = "/legal/politica-privacidad"
    terminos_url: str = "/legal/terminos-condiciones"


class DataExportOut(BaseModel):
    """User data export for Ley 1581 - Derecho de acceso."""
    user: UserOut
    orders_count: int
    sessions_count: int
    created_at: datetime