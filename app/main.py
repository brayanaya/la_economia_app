"""
Punto de entrada de la aplicacion FastAPI â€” La Economi­a Aya API.

Ejecucion local:
    uvicorn app.main:app --reload --port 8000

Documentacion interactiva generada automi¡ticamente por FastAPI:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.security import RateLimitMiddleware, SecurityHeadersMiddleware

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API del backend de negocio (monolito modular) del Supermercado "
        "La Economi­a Aya â€” sedes Santa Isabel y Machines, Neiva, Huila. "
        "Expone el cati¡logo unificado, la comparativa de inventario "
        "multisede, el endpoint de sincronizacion con Siigo y el "
        "retriever semi¡ntico del pipeline RAG del agente de IA."
    ),
    debug=settings.debug,
)

# Orden: CORS se registra al final para quedar como capa externa y cubrir tambien las respuestas 429.
app.add_middleware(
    RateLimitMiddleware,
    reglas={
        "/agente/chat": (10, 60),
        "/semantica": (30, 60),
        "/consentimiento": (20, 60),
    },
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modulo ordenes (carrito) ---
from app.ordenes.router import router as ordenes_router
app.include_router(ordenes_router, prefix="/api/v1")
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Salud"], summary="Health check")
async def raiz() -> dict[str, str]:
    return {
        "servicio": settings.app_name,
        "version": settings.app_version,
        "estado": "operativo",
    }
