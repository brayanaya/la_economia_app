import hashlib
import json
import secrets
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi import FastAPI
from app.auth.models import Customer, CustomerSession
from app.ordenes.models import Orden
from app.auth.router import router as auth_router, digest
from app.core.config import settings
from app.core.database import Base, get_db


@pytest.fixture
def auth_app():
    app = FastAPI()
    app.include_router(auth_router)
    return app


@pytest.fixture
async def auth_session_factory():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    Customer.__table__,
                    CustomerSession.__table__,
                    Orden.__table__,
                ],
            )
        )
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def auth_client(auth_app, auth_session_factory):
    async def _get_db():
        async with auth_session_factory() as session:
            yield session

    auth_app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=auth_app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        client.headers["Origin"] = settings.cors_origins[0]
        yield client


@pytest.mark.asyncio
async def test_register_and_login(auth_client):
    # 1. Registro exitoso
    payload = {
        "email": "estudiante.huila@usco.edu.co",
        "password": "PasswordSeguro123*",
        "nombre": "Estudiante Huilense",
        "telefono": "3101234567",
        "consentimiento_datos": True,
        "consentimiento_marketing": False,
    }
    resp = await auth_client.post("/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["user"]["email"] == "estudiante.huila@usco.edu.co"
    assert data["user"]["nombre"] == "Estudiante Huilense"
    assert "csrf_token" in data
    assert settings.auth_cookie_name in resp.cookies

    # 2. Email duplicado debe fallar con 409
    resp_dup = await auth_client.post("/auth/register", json=payload)
    assert resp_dup.status_code == 409

    # 3. Login exitoso
    resp_login = await auth_client.post(
        "/auth/login",
        json={"email": "estudiante.huila@usco.edu.co", "password": "PasswordSeguro123*"},
    )
    assert resp_login.status_code == 200
    assert resp_login.json()["user"]["email"] == "estudiante.huila@usco.edu.co"

    # 4. Login con contraseña errónea debe fallar con 401
    resp_wrong = await auth_client.post(
        "/auth/login",
        json={"email": "estudiante.huila@usco.edu.co", "password": "ClaveIncorrecta123*"},
    )
    assert resp_wrong.status_code == 401


@pytest.mark.asyncio
async def test_google_auth(auth_client):
    # Generar token JWT simulando Google OAuth ID Token
    google_payload = {
        "sub": "google-user-id-998877",
        "email": "opita.google@usco.edu.co",
        "name": "Usuario Google Opita",
        "picture": "https://lh3.googleusercontent.com/photo.jpg",
        "email_verified": True,
        "iss": "https://accounts.google.com",
    }
    fake_id_token = jwt.encode(google_payload, "mock-secret-test", algorithm="HS256")

    # Primera autenticación: debe registrar automáticamente al usuario con Google
    resp = await auth_client.post("/auth/google", json={"id_token": fake_id_token})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user"]["email"] == "opita.google@usco.edu.co"
    assert data["user"]["nombre"] == "Usuario Google Opita"
    assert data["user"]["google_linked"] is True
    assert settings.auth_cookie_name in resp.cookies

    # Segunda autenticación: debe iniciar sesión del usuario existente
    resp2 = await auth_client.post("/auth/google", json={"id_token": fake_id_token})
    assert resp2.status_code == 200
    assert resp2.json()["user"]["id"] == data["user"]["id"]


@pytest.mark.asyncio
async def test_magic_link_flow(auth_client):
    # Primero registrar usuario
    await auth_client.post(
        "/auth/register",
        json={
            "email": "magic@usco.edu.co",
            "password": "PasswordSeguro123*",
            "nombre": "Usuario Magico",
            "consentimiento_datos": True,
        },
    )

    # Solicitar magic link
    resp = await auth_client.post("/auth/magic-link", json={"email": "magic@usco.edu.co"})
    assert resp.status_code == 202
    dev_token = resp.json().get("dev_token")
    assert dev_token is not None

    # Verificar magic link
    resp_verify = await auth_client.post("/auth/magic-link/verify", json={"token": dev_token})
    assert resp_verify.status_code == 200
    assert resp_verify.json()["user"]["email"] == "magic@usco.edu.co"
    assert settings.auth_cookie_name in resp_verify.cookies


@pytest.mark.asyncio
async def test_ley_1581_habeas_data_and_profile(auth_client, auth_session_factory):
    # Registrar y autenticar
    reg_resp = await auth_client.post(
        "/auth/register",
        json={
            "email": "habeas.data@usco.edu.co",
            "password": "PasswordSeguro123*",
            "nombre": "Usuario Privacidad",
            "telefono": "3109998877",
            "consentimiento_datos": True,
            "consentimiento_marketing": False,
        },
    )
    auth_data = reg_resp.json()
    csrf_token = auth_data["csrf_token"]
    cookie_header = reg_resp.headers.get("set-cookie")

    # Configurar cliente autenticado
    auth_client.headers["X-CSRF-Token"] = csrf_token

    # 1. Consultar perfil propio (/auth/me)
    resp_me = await auth_client.get("/auth/me")
    assert resp_me.status_code == 200
    assert resp_me.json()["user"]["email"] == "habeas.data@usco.edu.co"

    # 2. Actualizar perfil y consentimientos
    resp_patch = await auth_client.patch(
        "/auth/me",
        json={"nombre": "Usuario Actualizado", "consentimiento_marketing": True},
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["nombre"] == "Usuario Actualizado"
    assert resp_patch.json()["consentimiento_marketing"] is True

    # 3. Exportar datos (Ley 1581 - Derecho de Acceso)
    resp_export = await auth_client.get("/auth/me/export")
    assert resp_export.status_code == 200
    export_json = resp_export.json()
    assert export_json["user"]["email"] == "habeas.data@usco.edu.co"
    assert "orders_count" in export_json

    # 4. Eliminar cuenta permanentemente (Ley 1581 - Derecho de Supresión)
    resp_del = await auth_client.delete("/auth/me")
    assert resp_del.status_code == 200
    assert "suprimidos" in resp_del.json()["mensaje"].lower()
