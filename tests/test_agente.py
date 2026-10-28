from decimal import Decimal
from unittest.mock import AsyncMock

from app.core.config import settings
from app.schemas.busqueda import ProductoRecuperado
from app.services import agente as servicio_agente
from app.services.llm import construir_proveedores
from app.services.agente import generar_respuesta_agente


def _producto(nombre="Leche Entera 1L", similitud=0.71):
    return ProductoRecuperado(
        producto_id="d1b60b9f-1111-4222-8333-444455556666",
        nombre=nombre,
        categoria_nombre="Lacteos",
        precio=Decimal("4500"),
        stock_sede=12,
        similitud=similitud,
    )


async def test_sin_llm_responde_de_forma_determinista_con_productos(monkeypatch):
    monkeypatch.setattr(servicio_agente, "generar_texto", AsyncMock(return_value=None))

    texto, por_llm = await generar_respuesta_agente("quiero leche", [_producto()])
    assert por_llm is False
    assert "Leche Entera 1L" in texto
    assert "4.500" in texto


async def test_sin_llm_y_sin_productos_saluda_o_pide_reformular(monkeypatch):
    monkeypatch.setattr(servicio_agente, "generar_texto", AsyncMock(return_value=None))

    saludo, _ = await generar_respuesta_agente("¡Hola, buenas tardes!", [])
    assert "La Economía Aya" in saludo

    desconocido, _ = await generar_respuesta_agente("dame lo que sea", [])
    assert "no encontré" in desconocido


async def test_con_llm_devuelve_su_texto(monkeypatch):
    monkeypatch.setattr(
        servicio_agente, "generar_texto", AsyncMock(return_value=" ¡Claro! Tengo leche entera. ")
    )

    texto, por_llm = await generar_respuesta_agente("quiero leche", [_producto()])
    assert por_llm is True
    assert texto == "¡Claro! Tengo leche entera."


async def test_proveedor_fallido_degrada_sin_excepcion(monkeypatch):
    monkeypatch.setattr(servicio_agente, "generar_texto", AsyncMock(side_effect=RuntimeError("ollama apagado")))

    texto, por_llm = await generar_respuesta_agente("hola", [_producto()])
    assert por_llm is False
    assert "Leche Entera 1L" in texto


async def test_construir_proveedores_segun_configuracion(monkeypatch):
    # Solo ollama
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    proveedores = construir_proveedores()
    assert [p.nombre for p in proveedores] == [f"ollama:{settings.llm_model}"]

    # anthropic sin API key: nadie
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    assert construir_proveedores() == []

    # auto con API key: Claude primero, luego ollama de respaldo
    monkeypatch.setattr(settings, "llm_provider", "auto")
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-test")
    proveedores = construir_proveedores()
    assert [p.nombre for p in proveedores] == [
        f"anthropic:{settings.anthropic_chat_model}",
        f"ollama:{settings.llm_model}",
    ]


async def test_el_historial_llega_al_llm(monkeypatch):
    capturado: dict = {}

    async def _generar(mensajes):
        capturado["mensajes"] = mensajes
        return "listo"

    monkeypatch.setattr(servicio_agente, "generar_texto", _generar)

    historial = [("usuario", "hola"), ("asistente", "¡Hola! ¿En qué te ayudo?")]
    _, por_llm = await generar_respuesta_agente("tienes arroz", [_producto()], historial)
    assert por_llm is True

    mensajes = capturado["mensajes"]
    roles = [mensaje["role"] for mensaje in mensajes]
    assert roles[0] == "system"
    assert roles[-1] == "user"
    assert roles.count("user") == 2 and roles.count("assistant") == 1
    assert "CONTEXTO" in mensajes[-1]["content"]
    assert "tienes arroz" in mensajes[-1]["content"]


async def test_clasificacion_de_intenciones():
    from app.api.v1.endpoints.agente import _clasificar_intencion
    from app.services.agente import normalizar_texto

    assert _clasificar_intencion(normalizar_texto("¡Hola!")) == "saludo"
    assert _clasificar_intencion(normalizar_texto("Buenas tardes")) == "saludo"
    assert _clasificar_intencion(normalizar_texto("¿Qué más pues?")) == "saludo"
    assert _clasificar_intencion(normalizar_texto("Muchas gracias")) == "despedida"
    assert _clasificar_intencion(normalizar_texto("¿Cómo puedo pagar el pedido?")) == "faq"
    assert _clasificar_intencion(normalizar_texto("¿Qué puedo hacer de desayuno?")) == "receta"
    assert _clasificar_intencion(normalizar_texto("Se me antoja algo dulce")) == "receta"
    assert _clasificar_intencion(normalizar_texto("Hola, ¿tienen arroz?")) == "busqueda"
    assert _clasificar_intencion(normalizar_texto("¿Cuánto vale la leche?")) == "busqueda"


async def test_receta_amplia_consultas_por_ingrediente():
    from app.api.v1.endpoints.agente import _consultas_recuperacion

    consultas = _consultas_recuperacion("¿Qué puedo hacer de desayuno?", intencion="receta")
    textos = [consulta for consulta, _ in consultas]
    assert textos[0] == "¿Qué puedo hacer de desayuno?"
    assert "huevos" in textos and "arepa" in textos and "cafe" in textos
    assert len(consultas) <= 9

    pericos = _consultas_recuperacion("¿Cómo hago huevos pericos?", intencion="receta")
    textos = [consulta for consulta, _ in pericos]
    for ingrediente in ("huevos", "tomate", "cebolla larga", "sal"):
        assert ingrediente in textos

    # En una busqueda normal no se amplian consultas.
    assert _consultas_recuperacion("tienes arroz") == [("tienes arroz", 8)]


async def test_saludos_y_faq_responden_sin_gastar_el_retriever(monkeypatch):
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from app.api.v1.endpoints import agente as endpoint_agente

    embedding = AsyncMock(return_value=[0.1] * 8)
    monkeypatch.setattr(endpoint_agente, "get_embedding", embedding)
    monkeypatch.setattr(servicio_agente, "generar_texto", AsyncMock(return_value=None))

    app = FastAPI()
    app.include_router(endpoint_agente.router, prefix="/api/v1/agente")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        for mensaje, fragmento in (
            ("hola", "La Economía Aya"),
            ("buenos días", "La Economía Aya"),
            ("muchas gracias", "Con gusto"),
            ("¿cómo puedo pagar el pedido?", "contra entrega"),
        ):
            respuesta = await cliente.post("/api/v1/agente/chat", json={"mensaje": mensaje})
            assert respuesta.status_code == 200, respuesta.text
            data = respuesta.json()
            assert fragmento in data["respuesta"]
            assert data["productos_recomendados"] == []
            assert data["hubo_resultados_relevantes"] is False

    embedding.assert_not_called()


async def test_endpoint_del_agente_sigue_vivo_si_el_retriever_falla(monkeypatch):
    """
    El chat responde 200 (con el respondedor determinista) aunque no haya
    embeddings ni LLM disponibles: nunca se cae el servicio.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from app.api.v1.endpoints.agente import router as agente_router

    # Ollama en un puerto cerrado: get_embedding falla rapido y el
    # retriever best-effort devuelve [] sin romper el endpoint.
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:9")
    monkeypatch.setattr(settings, "llm_provider", "ollama")

    app = FastAPI()
    app.include_router(agente_router, prefix="/api/v1/agente")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        respuesta = await cliente.post(
            "/api/v1/agente/chat",
            json={"mensaje": "hola, que tienes", "historial": []},
        )
        assert respuesta.status_code == 200, respuesta.text
        data = respuesta.json()
        assert data["respuesta"]
        assert data["generado_por_llm"] is False
        assert data["hubo_resultados_relevantes"] is False
        assert data["productos_recomendados"] == []
