from fastapi import APIRouter

from app.api.v1.endpoints import busqueda, productos, inventario, agente, legal

api_router = APIRouter()
api_router.include_router(busqueda.router, prefix="/busqueda", tags=["Busqueda Semantica"])
api_router.include_router(productos.router, prefix="/productos", tags=["Productos"])
api_router.include_router(inventario.router, prefix="/inventario", tags=["Inventario"])
api_router.include_router(agente.router, prefix="/agente", tags=["Agente RAG"])
api_router.include_router(legal.router, prefix="/legal", tags=["Cumplimiento Legal (Ley 1581)"])
