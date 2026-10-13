import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.ordenes.models import DetalleOrden, Orden
from app.ordenes.router import router as ordenes_router


@pytest_asyncio.fixture
async def session_factory():
    """Base SQLite en memoria con solo las tablas del modulo de ordenes."""
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, tables=[Orden.__table__, DetalleOrden.__table__]
            )
        )
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory):
    """Cliente HTTP contra una app minima con solo el router de ordenes."""
    app = FastAPI()
    app.include_router(ordenes_router, prefix="/api/v1")

    async def _get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
