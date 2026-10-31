import hashlib
import hmac
import secrets
import uuid
import base64
import pyotp
import qrcode
import io
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from app.core.config import settings
from app.core.database import get_db
from app.auth.models import Customer, CustomerSession
from app.auth.schemas import (
    RegisterIn,
    LoginIn,
    GoogleAuthIn,
    MagicLinkIn,
    MagicLinkVerifyIn,
    TotpSetupOut,
    TotpVerifyIn,
    TotpStatusOut,
    UserOut,
    UserUpdateIn,
    AuthOut,
    ConsentOut,
    DataExportOut,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

hasher = PasswordHasher(type=Type.ID)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def fail():
    raise HTTPException(status_code=401, detail="Credenciales inválidas")


def origin_ok(request: Request):
    origin = request.headers.get("origin")
    if not origin or origin not in settings.cors_origins:
        raise HTTPException(403, "Origen no permitido")


async def issue(user: Customer, db: AsyncSession, response: Response, requires_totp: bool = False) -> AuthOut:
    raw = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    db.add(
        CustomerSession(
            user_id=user.id,
            token_hash=digest(raw),
            csrf_token=csrf,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.auth_session_ttl_seconds),
        )
    )
    await db.commit()
    response.set_cookie(
        settings.auth_cookie_name,
        raw,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=settings.auth_session_ttl_seconds,
        path="/",
    )
    return AuthOut(
        user=UserOut(
            id=str(user.id),
            email=user.email,
            nombre=user.nombre,
            telefono=user.telefono,
            fecha_nacimiento=user.fecha_nacimiento,
            totp_enabled=user.totp_enabled,
            google_linked=bool(user.google_sub),
            consentimiento_datos=user.consentimiento_datos,
            consentimiento_marketing=user.consentimiento_marketing,
        ),
        csrf_token=csrf,
        requires_totp=requires_totp,
    )


async def current_session(request: Request, db: AsyncSession = Depends(get_db)):
    raw = request.cookies.get(settings.auth_cookie_name)
    if not raw:
        raise HTTPException(401, "Autenticación requerida")
    result = await db.execute(
        select(CustomerSession).where(
            CustomerSession.token_hash == digest(raw),
            CustomerSession.expires_at > datetime.now(timezone.utc),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(401, "Autenticación requerida")
    return session


async def current_user(session: CustomerSession = Depends(current_session), db: AsyncSession = Depends(get_db)):
    return await db.get(Customer, session.user_id)


def check_csrf(request: Request, session: CustomerSession):
    origin_ok(request)
    supplied = request.headers.get("x-csrf-token", "")
    if not hmac.compare_digest(digest(supplied), digest(session.csrf_token)):
        raise HTTPException(403, "CSRF token inválido")


def verify_google_id_token(id_token: str) -> Optional[dict]:
    """Verify Google ID token and return payload. Returns None if invalid."""
    try:
        # In production, use google-auth library:
        # from google.oauth2 import id_token as google_id_token
        # from google.auth.transport import requests
        # payload = google_id_token.verify_oauth2_token(
        #     id_token, requests.Request(), settings.google_client_id
        # )
        # For now, decode JWT manually (not secure, just for structure)
        import jwt
        # Don't verify signature in dev - in production MUST verify with Google's public keys
        payload = jwt.decode(id_token, options={"verify_signature": False})
        return payload
    except Exception:
        return None


def generate_magic_token() -> str:
    return secrets.token_urlsafe(32)


def verify_totp(secret: str, code: str) -> bool:
    """Verify TOTP code against secret."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_uri(secret: str, email: str, issuer: str = "La Economía Aya") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def generate_qr_code(data: str) -> str:
    """Generate QR code as base64 PNG."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ==================== REGISTRO / LOGIN ====================

@router.post("/register", response_model=AuthOut, status_code=201)
async def register(data: RegisterIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    origin_ok(request)
    user = Customer(
        email=data.email,
        nombre=data.nombre.strip(),
        password_hash=hasher.hash(data.password),
        telefono=data.telefono,
        consentimiento_datos=data.consentimiento_datos,
        consentimiento_marketing=data.consentimiento_marketing,
        consentimiento_fecha=datetime.now(timezone.utc) if data.consentimiento_datos else None,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "No fue posible crear la cuenta (email ya registrado)")
    return await issue(user, db, response)


@router.post("/login", response_model=AuthOut)
async def login(data: LoginIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    origin_ok(request)
    result = await db.execute(select(Customer).where(Customer.email == data.email))
    user = result.scalar_one_or_none()

    try:
        if not user:
            # Timing attack prevention
            hasher.verify(hasher.hash("dummy-password-for-timing"), data.password)
            fail()
        if user.password_hash:
            hasher.verify(user.password_hash, data.password)
        else:
            # User registered with Google OAuth, no password
            fail()
    except (VerifyMismatchError, InvalidHashError):
        fail()

    # Check if TOTP is enabled
    if user.totp_enabled:
        if not data.totp_code:
            return AuthOut(
                user=UserOut(
                    id=str(user.id),
                    email=user.email,
                    nombre=user.nombre,
                    telefono=user.telefono,
                    fecha_nacimiento=user.fecha_nacimiento,
                    totp_enabled=True,
                    google_linked=bool(user.google_sub),
                    consentimiento_datos=user.consentimiento_datos,
                    consentimiento_marketing=user.consentimiento_marketing,
                ),
                csrf_token="",
                requires_totp=True,
            )
        if not verify_totp(user.totp_secret, data.totp_code):
            raise HTTPException(401, "Código 2FA inválido")

    return await issue(user, db, response)


# ==================== GOOGLE OAUTH ====================

@router.post("/google", response_model=AuthOut)
async def google_auth(data: GoogleAuthIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Login/Register with Google OAuth (ID token from frontend)."""
    origin_ok(request)

    payload = verify_google_id_token(data.id_token)
    if not payload:
        raise HTTPException(401, "Token de Google inválido")

    google_sub = payload.get("sub")
    google_email = payload.get("email", "").lower()
    google_nombre = payload.get("name", "")
    google_picture = payload.get("picture")

    if not google_sub or not google_email:
        raise HTTPException(400, "Token de Google incompleto")

    # Try to find existing user by google_sub
    result = await db.execute(select(Customer).where(Customer.google_sub == google_sub))
    user = result.scalar_one_or_none()

    if user:
        # Existing Google user - update info
        user.google_email = google_email
        user.google_nombre = google_nombre
        user.google_avatar_url = google_picture
        await db.commit()
        return await issue(user, db, response)

    # Try to find by email
    result = await db.execute(select(Customer).where(Customer.email == google_email))
    user = result.scalar_one_or_none()

    if user:
        # Link Google account to existing email user
        user.google_sub = google_sub
        user.google_email = google_email
        user.google_nombre = google_nombre
        user.google_avatar_url = google_picture
        await db.commit()
        return await issue(user, db, response)

    # Create new user with Google
    user = Customer(
        email=google_email,
        nombre=google_nombre or google_email.split("@")[0],
        password_hash=None,  # No password for Google users
        google_sub=google_sub,
        google_email=google_email,
        google_nombre=google_nombre,
        google_avatar_url=google_picture,
        consentimiento_datos=True,
        consentimiento_fecha=datetime.now(timezone.utc),
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Error al crear cuenta con Google")

    return await issue(user, db, response)


# ==================== MAGIC LINK (PASSWORDLESS) ====================

# In-memory store for magic links (in production use Redis with TTL)
_magic_links = {}


@router.post("/magic-link", status_code=202)
async def request_magic_link(data: MagicLinkIn, db: AsyncSession = Depends(get_db)):
    """Send magic link for passwordless login (email only)."""
    result = await db.execute(select(Customer).where(Customer.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal if email exists
        return {"ok": True, "mensaje": "Si el email existe, recibirás un enlace mágico"}

    token = generate_magic_token()
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    _magic_links[token] = {"email": data.email, "expires": expires}

    # In production: send email with link
    # await send_email(user.email, "Tu enlace mágico", f"https://app.laeconomiaaya.com/auth/magic?token={token}")

    return {"ok": True, "mensaje": "Enlace mágico enviado (en desarrollo: ver logs)", "dev_token": token}


@router.post("/magic-link/verify", response_model=AuthOut)
async def verify_magic_link(data: MagicLinkVerifyIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Verify magic link token and log in."""
    origin_ok(request)

    link_data = _magic_links.get(data.token)
    if not link_data:
        raise HTTPException(400, "Enlace inválido o expirado")

    if datetime.now(timezone.utc) > link_data["expires"]:
        del _magic_links[data.token]
        raise HTTPException(400, "Enlace expirado")

    email = link_data["email"]
    del _magic_links[data.token]

    result = await db.execute(select(Customer).where(Customer.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    # Check TOTP if enabled
    if user.totp_enabled:
        return AuthOut(
            user=UserOut(
                id=str(user.id),
                email=user.email,
                nombre=user.nombre,
                telefono=user.telefono,
                fecha_nacimiento=user.fecha_nacimiento,
                totp_enabled=True,
                google_linked=bool(user.google_sub),
                consentimiento_datos=user.consentimiento_datos,
                consentimiento_marketing=user.consentimiento_marketing,
            ),
            csrf_token="",
            requires_totp=True,
        )

    return await issue(user, db, response)


# ==================== TOTP / GOOGLE AUTHENTICATOR ====================

@router.post("/totp/setup", response_model=TotpSetupOut)
async def setup_totp(session: CustomerSession = Depends(current_session), db: AsyncSession = Depends(get_db)):
    """Generate TOTP secret and QR code for Google Authenticator."""
    user = await db.get(Customer, session.user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    if user.totp_enabled:
        raise HTTPException(400, "2FA ya está activado. Desactívalo primero si quieres regenerar.")

    secret = generate_totp_secret()
    uri = build_totp_uri(secret, user.email)
    qr_code_url = f"data:image/png;base64,{generate_qr_code(uri)}"

    # Store secret temporarily (user must verify to enable)
    user.totp_secret = secret
    await db.commit()

    return TotpSetupOut(secret=secret, uri=uri, qr_code_url=qr_code_url)


@router.post("/totp/verify")
async def verify_totp_setup(data: TotpVerifyIn, session: CustomerSession = Depends(current_session), db: AsyncSession = Depends(get_db)):
    """Verify TOTP code and enable 2FA."""
    user = await db.get(Customer, session.user_id)
    if not user or not user.totp_secret:
        raise HTTPException(400, "No hay configuración 2FA pendiente")

    if not verify_totp(user.totp_secret, data.code):
        raise HTTPException(401, "Código inválido")

    user.totp_enabled = True
    await db.commit()

    return {"ok": True, "mensaje": "2FA activado correctamente con Google Authenticator"}


@router.post("/totp/disable")
async def disable_totp(data: TotpVerifyIn, session: CustomerSession = Depends(current_session), db: AsyncSession = Depends(get_db)):
    """Disable TOTP/2FA (requires current code)."""
    user = await db.get(Customer, session.user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    if not user.totp_enabled:
        raise HTTPException(400, "2FA no está activado")

    if not verify_totp(user.totp_secret, data.code):
        raise HTTPException(401, "Código inválido")

    user.totp_enabled = False
    user.totp_secret = None
    await db.commit()

    return {"ok": True, "mensaje": "2FA desactivado"}


@router.get("/totp/status", response_model=TotpStatusOut)
async def totp_status(session: CustomerSession = Depends(current_session), db: AsyncSession = Depends(get_db)):
    """Check if TOTP is enabled."""
    user = await db.get(Customer, session.user_id)
    return TotpStatusOut(enabled=user.totp_enabled if user else False)


# ==================== PERFIL Y CONSENTIMIENTO ====================

@router.get("/me", response_model=AuthOut)
async def me(session: CustomerSession = Depends(current_session), user: Customer = Depends(current_user)):
    return AuthOut(
        user=UserOut(
            id=str(user.id),
            email=user.email,
            nombre=user.nombre,
            telefono=user.telefono,
            fecha_nacimiento=user.fecha_nacimiento,
            totp_enabled=user.totp_enabled,
            google_linked=bool(user.google_sub),
            consentimiento_datos=user.consentimiento_datos,
            consentimiento_marketing=user.consentimiento_marketing,
        ),
        csrf_token=session.csrf_token,
        requires_totp=False,
    )


@router.patch("/me", response_model=UserOut)
async def update_profile(
    data: UserUpdateIn,
    session: CustomerSession = Depends(current_session),
    user: Customer = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    check_csrf(Request({"type": "http", "headers": {}}), session)  # Skip origin check for API calls

    if data.nombre is not None:
        user.nombre = data.nombre.strip()
    if data.telefono is not None:
        user.telefono = data.telefono
    if data.consentimiento_datos is not None:
        user.consentimiento_datos = data.consentimiento_datos
        if data.consentimiento_datos and not user.consentimiento_fecha:
            user.consentimiento_fecha = datetime.now(timezone.utc)
    if data.consentimiento_marketing is not None:
        user.consentimiento_marketing = data.consentimiento_marketing

    await db.commit()
    await db.refresh(user)

    return UserOut(
        id=str(user.id),
        email=user.email,
        nombre=user.nombre,
        telefono=user.telefono,
        fecha_nacimiento=user.fecha_nacimiento,
        totp_enabled=user.totp_enabled,
        google_linked=bool(user.google_sub),
        consentimiento_datos=user.consentimiento_datos,
        consentimiento_marketing=user.consentimiento_marketing,
    )


@router.get("/consent", response_model=ConsentOut)
async def get_consent(user: Customer = Depends(current_user)):
    """Get consent info for Ley 1581 compliance."""
    return ConsentOut(
        consentimiento_datos=user.consentimiento_datos,
        consentimiento_marketing=user.consentimiento_marketing,
        consentimiento_fecha=user.consentimiento_fecha,
    )


@router.delete("/me")
async def delete_account(
    session: CustomerSession = Depends(current_session),
    user: Customer = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete account (Ley 1581 - Derecho de supresión)."""
    await db.delete(user)
    await db.commit()
    return {"ok": True, "mensaje": "Cuenta eliminada. Tus datos han sido suprimidos según Ley 1581."}


@router.get("/me/export", response_model=DataExportOut)
async def export_data(user: Customer = Depends(current_user), db: AsyncSession = Depends(get_db)):
    """Export user data (Ley 1581 - Derecho de acceso)."""
    from app.ordenes.models import Orden
    from sqlalchemy import func

    orders_result = await db.execute(select(func.count(Orden.id)).where(Orden.customer_id == user.id))
    orders_count = orders_result.scalar() or 0

    sessions_result = await db.execute(
        select(func.count(CustomerSession.id)).where(CustomerSession.user_id == user.id)
    )
    sessions_count = sessions_result.scalar() or 0

    return DataExportOut(
        user=UserOut(
            id=str(user.id),
            email=user.email,
            nombre=user.nombre,
            telefono=user.telefono,
            fecha_nacimiento=user.fecha_nacimiento,
            totp_enabled=user.totp_enabled,
            google_linked=bool(user.google_sub),
            consentimiento_datos=user.consentimiento_datos,
            consentimiento_marketing=user.consentimiento_marketing,
        ),
        orders_count=orders_count,
        sessions_count=sessions_count,
        created_at=user.consentimiento_fecha or datetime.now(timezone.utc),
    )


# ==================== LOGOUT ====================

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: CustomerSession = Depends(current_session),
    db: AsyncSession = Depends(get_db),
):
    check_csrf(request, session)
    await db.delete(session)
    await db.commit()
    response.delete_cookie(
        settings.auth_cookie_name, path="/", httponly=True, secure=settings.auth_cookie_secure, samesite="lax"
    )
    return {"ok": True}