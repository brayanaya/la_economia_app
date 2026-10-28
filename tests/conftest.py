import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.auth.models import Customer, CustomerSession
from app.core.config import settings
from app.core.database import Base, get_db
from app.ordenes.models import DetalleOrden, Orden
from app.ordenes.router import router as ordenes_router
from app.pagos.models import Pago
from app.pagos.router import router as pagos_router


@pytest_asyncio.fixture
async def session_factory():
    """Base SQLite en memoria con las tablas de clientes, ordenes y pagos."""
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    Customer.__table__,
                    CustomerSession.__table__,
                    Orden.__table__,
                    DetalleOrden.__table__,
                    Pago.__table__,
                ],
            )
        )
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def _sembrar_cliente(session_factory, email="cliente@test.local"):
    """Crea un cliente con sesion activa; devuelve (cookie_raw, csrf_token)."""
    async with session_factory() as session:
        cookie_cruda = secrets.token_urlsafe(32)
        usuario = Customer(
            id=uuid.uuid4(),
            email=email,
            nombre="Cliente Prueba",
            password_hash="hash-irrelevante-para-tests",
        )
        sesion = CustomerSession(
            id=uuid.uuid4(),
            user_id=usuario.id,
            token_hash=hashlib.sha256(cookie_cruda.encode()).hexdigest(),
            csrf_token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        session.add_all([usuario, sesion])
        await session.commit()
        return usuario.id, cookie_cruda, sesion.csrf_token


def _armar_app() -> FastAPI:
    """App minima con los routers que usan los tests (ordenes + pagos)."""
    app = FastAPI()
    app.include_router(ordenes_router, prefix="/api/v1")
    app.include_router(pagos_router, prefix="/api/v1")
    return app


@pytest_asyncio.fixture
async def cliente_autenticado(session_factory):
    """
    Cliente HTTP autenticado: lleva la cookie de sesion, el Origin permitido
    y el token CSRF que exigen los endpoints de escritura (crear orden, iniciar pago).
    """
    _, cookie_cruda, csrf = await _sembrar_cliente(session_factory)
    app = _armar_app()

    async def _get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cliente:
        cliente.headers["Cookie"] = f"{settings.auth_cookie_name}={cookie_cruda}"
        cliente.headers["Origin"] = settings.cors_origins[0]
        cliente.headers["X-CSRF-Token"] = csrf
        yield cliente


@pytest_asyncio.fixture
async def fabrica_clientes(session_factory):
    """
    Fabrica de clientes autenticados independientes (para probar permisos
    entre cuentas, p.ej. pagar una orden ajena). Uso:

        crear = await fabrica_clientes
        cliente_a = await crear("a@test.local")
        cliente_b = await crear("b@test.local")
    """
    clientes = []

    async def _crear(email: str) -> AsyncClient:
        _, cookie_cruda, csrf = await _sembrar_cliente(session_factory, email=email)
        app = _armar_app()

        async def _get_db():
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = _get_db
        transport = ASGITransport(app=app)
        cliente = AsyncClient(transport=transport, base_url="http://test")
        cliente.headers["Cookie"] = f"{settings.auth_cookie_name}={cookie_cruda}"
        cliente.headers["Origin"] = settings.cors_origins[0]
        cliente.headers["X-CSRF-Token"] = csrf
        clientes.append(cliente)
        return cliente

    yield _crear
    for cliente in clientes:
        await cliente.aclose()


@pytest_asyncio.fixture
async def client(session_factory):
    """Cliente HTTP sin autenticar (endpoints publicos: consulta, webhook)."""
    app = _armar_app()

    async def _get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
