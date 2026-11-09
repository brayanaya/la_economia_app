"""
Pruebas exhaustivas para Memoria Conversacional Persistente (Bloque 3).
Verifica:
- Creación de conversaciones en PostgreSQL
- Persistencia de mensajes
- Aislamiento entre usuarios
- Intento de acceso no autorizado
- Resumen automático cuando supera el umbral
- Supresión según Ley 1581 (eliminación de conversaciones)
"""
import uuid
import pytest
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.auth.models import Customer
from app.models.conversacion import Conversacion, Mensaje, TipoRemitente
from app.services.conversation.memory import (
    ConversationMemoryManager,
    ContextoConversacion,
    MensajeConversacion,
    RolMensaje,
)


@pytest.fixture
async def usuarios_test():
    """Crea dos usuarios de prueba en la base de datos para pruebas de aislamiento."""
    async with AsyncSessionLocal() as db:
        u1_id = uuid.uuid4()
        u2_id = uuid.uuid4()
        u1 = Customer(id=u1_id, email=f"user1_{u1_id.hex[:6]}@test.com", nombre="Usuario Uno")
        u2 = Customer(id=u2_id, email=f"user2_{u2_id.hex[:6]}@test.com", nombre="Usuario Dos")
        db.add_all([u1, u2])
        await db.commit()

    yield str(u1_id), str(u2_id)

    # Limpieza
    async with AsyncSessionLocal() as db:
        user1 = await db.get(Customer, u1_id)
        user2 = await db.get(Customer, u2_id)
        if user1:
            await db.delete(user1)
        if user2:
            await db.delete(user2)
        await db.commit()


@pytest.mark.asyncio
async def test_creacion_y_persistencia_mensajes(usuarios_test):
    user1_id, _ = usuarios_test
    async with AsyncSessionLocal() as db:
        manager = ConversationMemoryManager(db)
        
        # 1. Crear conversación
        ctx = await manager.obtener_o_crear(usuario_id=user1_id)
        cid = ctx.conversacion_id
        assert cid is not None
        assert ctx.usuario_id == user1_id
        
        # 2. Agregar mensaje usuario y respuesta asistente
        msg1 = MensajeConversacion(rol=RolMensaje.USUARIO, contenido="Quiero comprar café")
        msg2 = MensajeConversacion(rol=RolMensaje.ASISTENTE, contenido="Te recomiendo Café Sello Rojo 500g")
        ctx.agregar_mensaje(msg1)
        ctx.agregar_mensaje(msg2)
        await manager.guardar(ctx)
        
    # 3. Verificar persistencia en una nueva sesión
    async with AsyncSessionLocal() as db2:
        manager2 = ConversationMemoryManager(db2)
        ctx_recuperado = await manager2.obtener_o_crear(conversacion_id=cid, usuario_id=user1_id)
        assert len(ctx_recuperado.mensajes) == 2
        assert ctx_recuperado.mensajes[0].contenido == "Quiero comprar café"
        assert ctx_recuperado.mensajes[1].contenido == "Te recomiendo Café Sello Rojo 500g"


@pytest.mark.asyncio
async def test_aislamiento_entre_usuarios(usuarios_test):
    user1_id, user2_id = usuarios_test
    async with AsyncSessionLocal() as db:
        manager = ConversationMemoryManager(db)
        
        # Crear conversación para usuario 1
        ctx1 = await manager.obtener_o_crear(usuario_id=user1_id)
        cid1 = ctx1.conversacion_id
        msg = MensajeConversacion(rol=RolMensaje.USUARIO, contenido="Mensaje secreto de usuario 1")
        ctx1.agregar_mensaje(msg)
        await manager.guardar(ctx1)

    # Usuario 2 intenta acceder a la conversación de Usuario 1 -> Debe fallar o no encontrarla
    async with AsyncSessionLocal() as db2:
        manager2 = ConversationMemoryManager(db2)
        with pytest.raises(ValueError, match="no encontrada o no autorizada"):
            await manager2.obtener_historial_para_llm(conversacion_id=cid1, usuario_id=user2_id)


@pytest.mark.asyncio
async def test_eliminacion_derecho_al_olvido_ley_1581(usuarios_test):
    user1_id, _ = usuarios_test
    async with AsyncSessionLocal() as db:
        manager = ConversationMemoryManager(db)
        
        ctx = await manager.obtener_o_crear(usuario_id=user1_id)
        cid = ctx.conversacion_id
        ctx.agregar_mensaje(MensajeConversacion(rol=RolMensaje.USUARIO, contenido="Deseo eliminar mi cuenta y chats"))
        await manager.guardar(ctx)
        
        # Eliminar conversación
        eliminado = await manager.eliminar(cid, user1_id)
        assert eliminado is True

    # Verificar que ya no existe en la BD
    async with AsyncSessionLocal() as db2:
        manager2 = ConversationMemoryManager(db2)
        eliminado_otra_vez = await manager2.eliminar(cid, user1_id)
        assert eliminado_otra_vez is False


@pytest.mark.asyncio
async def test_resumen_automatico_umbral(usuarios_test):
    user1_id, _ = usuarios_test
    async with AsyncSessionLocal() as db:
        manager = ConversationMemoryManager(db)
        manager.resumen_umbral = 4  # Ajustar umbral para la prueba
        
        ctx = await manager.obtener_o_crear(usuario_id=user1_id)
        ctx.receta_actual = "huevos_pericos"
        ctx.productos_recientes = ["huevos", "cebolla", "tomate"]
        
        for i in range(5):
            ctx.agregar_mensaje(MensajeConversacion(rol=RolMensaje.USUARIO, contenido=f"Mensaje {i}"))
            
        await manager.guardar(ctx)
        assert ctx.resumen is not None
        assert "huevos_pericos" in ctx.resumen or "productos" in ctx.resumen


@pytest.mark.asyncio
async def test_aislamiento_visitantes_anonimos():
    """Verifica que el endpoint /conversaciones no liste chats a visitantes anónimos."""
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from app.api.v1.endpoints.agente import router as agente_router

    app = FastAPI()
    app.include_router(agente_router, prefix="/api/v1/agente")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        # Petición sin cookies de sesión (visitante anónimo)
        resp = await cliente.get("/api/v1/agente/conversaciones")
        assert resp.status_code == 200
        # No debe devolver ninguna conversación ajena ni de otros invitados
        assert resp.json() == []
