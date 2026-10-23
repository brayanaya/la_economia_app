import hashlib, hmac, secrets, uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from app.core.config import settings
from app.core.database import get_db
from .models import Customer, CustomerSession
from .schemas import AuthOut, LoginIn, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["Autenticacion"]); hasher=PasswordHasher(type=Type.ID)
def digest(value: str) -> str: return hashlib.sha256(value.encode()).hexdigest()
def fail(): raise HTTPException(status_code=401, detail="Credenciales invalidas")
def origin_ok(request: Request):
    origin=request.headers.get("origin")
    if not origin or origin not in settings.cors_origins: raise HTTPException(403, "Origen no permitido")
async def issue(user, db, response):
    raw=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32)
    db.add(CustomerSession(user_id=user.id, token_hash=digest(raw), csrf_token=csrf, expires_at=datetime.now(timezone.utc)+timedelta(seconds=settings.auth_session_ttl_seconds)))
    await db.commit()
    response.set_cookie(settings.auth_cookie_name, raw, httponly=True, secure=settings.auth_cookie_secure, samesite="lax", max_age=settings.auth_session_ttl_seconds, path="/")
    return AuthOut(user=UserOut(id=str(user.id), email=user.email, nombre=user.nombre), csrf_token=csrf)
async def current_session(request: Request, db: AsyncSession = Depends(get_db)):
    raw=request.cookies.get(settings.auth_cookie_name)
    if not raw: raise HTTPException(401, "Autenticacion requerida")
    result=await db.execute(select(CustomerSession).where(CustomerSession.token_hash==digest(raw), CustomerSession.expires_at>datetime.now(timezone.utc)))
    session=result.scalar_one_or_none()
    if not session: raise HTTPException(401, "Autenticacion requerida")
    return session
async def current_user(session: CustomerSession = Depends(current_session), db: AsyncSession = Depends(get_db)):
    return await db.get(Customer, session.user_id)
def check_csrf(request, session):
    origin_ok(request); supplied=request.headers.get("x-csrf-token", "")
    if not hmac.compare_digest(digest(supplied), digest(session.csrf_token)): raise HTTPException(403, "CSRF token invalido")

@router.post("/register", response_model=AuthOut, status_code=201)
async def register(data: RegisterIn, request: Request, response: Response, db: AsyncSession=Depends(get_db)):
    origin_ok(request)
    user=Customer(email=data.email, nombre=data.nombre.strip(), password_hash=hasher.hash(data.password))
    db.add(user)
    try: await db.flush()
    except IntegrityError:
        await db.rollback(); raise HTTPException(409, "No fue posible crear la cuenta")
    result=await issue(user, db, response); response.headers["Cache-Control"]="no-store"; return result

@router.post("/login", response_model=AuthOut)
async def login(data: LoginIn, request: Request, response: Response, db: AsyncSession=Depends(get_db)):
    origin_ok(request)
    result=await db.execute(select(Customer).where(Customer.email==data.email)); user=result.scalar_one_or_none()
    try:
        if not user: hasher.verify(hasher.hash("dummy-password-for-timing"), data.password); fail()
        hasher.verify(user.password_hash, data.password)
    except (VerifyMismatchError, InvalidHashError): fail()
    value=await issue(user, db, response); response.headers["Cache-Control"]="no-store"; return value

@router.get("/me", response_model=AuthOut)
async def me(session: CustomerSession=Depends(current_session), user: Customer=Depends(current_user)):
    # Never return the opaque session credential; rotate CSRF value atomically on client request is unnecessary.
    return AuthOut(user=UserOut(id=str(user.id), email=user.email, nombre=user.nombre), csrf_token=session.csrf_token)

@router.post("/logout")
async def logout(request: Request, response: Response, session: CustomerSession=Depends(current_session), db: AsyncSession=Depends(get_db)):
    check_csrf(request, session); await db.delete(session); await db.commit()
    response.delete_cookie(settings.auth_cookie_name, path="/", httponly=True, secure=settings.auth_cookie_secure, samesite="lax")
    return {"ok": True}
