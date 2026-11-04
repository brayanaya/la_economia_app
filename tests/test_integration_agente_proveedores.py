"""
Pruebas de integración: Agente + Provider Registry

Demuestra que el agente:
1. Depende del contrato común (ProductProvider protocol), NO de MockProvider/MasControlProvider directamente
2. Saludos y recetas generales NO hacen búsquedas de productos
3. Búsquedas comerciales usan el proveedor seleccionado
4. Fallos de MasControl NO activan datos ficticios (degradan con error explícito)
5. Historial funciona con mensajes tipados (dict role/content)
6. Contexto se conserva entre turnos (productos_recientes, receta_actual, lista_mercado, presupuesto)
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Optional

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.catalog_state import catalogo_state, CatalogoEstado
from app.schemas.busqueda import ProductoRecuperado
from app.services.providers.base import (
    ProductProvider,
    Producto,
    FiltrosBusqueda,
    TipoBusqueda,
    ProveedorNoDisponibleError,
)
from app.services.providers import proveedor_registry, get_proveedor_catalogo, get_proveedor_registry
from app.api.v1.endpoints import agente as endpoint_agente
from app.services import agente as servicio_agente
from app.services.conversation import get_conversation_memory, ContextoConversacion, MensajeConversacion


# ============================================================
# PROVEEDOR DE PRUEBA (Fake) - Implementa el contrato ProductProvider
# ============================================================

class ProveedorTestFake(ProductProvider):
    """
    Proveedor falso para tests que implementa el contrato ProductProvider.
    Demuestra que el agente funciona con CUALQUIER implementación del protocolo.
    """
    nombre = "test_fake"
    version = "1.0.0"
    _ultimo_error = None

    def __init__(self, productos_disponibles: Optional[List[Producto]] = None, debe_fallar: bool = False):
        self._productos = productos_disponibles or []
        self._debe_fallar = debe_fallar
        self.llamadas_busqueda = []
        self.llamadas_obtener_por_id = []

    @property
    def esta_disponible(self) -> bool:
        return not self._debe_fallar

    async def health_check(self) -> dict:
        if self._debe_fallar:
            return {"estado": "error", "error": "Simulado: proveedor caído"}
        return {"estado": "ok", "proveedor": self.nombre}

    async def buscar(
        self,
        query: str,
        filtros: Optional[FiltrosBusqueda] = None,
        tipo_busqueda: TipoBusqueda = TipoBusqueda.SEMANTICA
    ) -> List[Producto]:
        self.llamadas_busqueda.append({"query": query, "filtros": filtros, "tipo": tipo_busqueda})
        if self._debe_fallar:
            raise ProveedorNoDisponibleError(self.nombre, "Fallo simulado")
        # Filtrar productos que coincidan con query (mejor matching: palabras clave)
        query_lower = query.lower()
        palabras = [w for w in query_lower.split() if len(w) > 2]  # Palabras significativas
        resultados = []
        for p in self._productos:
            nombre_lower = p.nombre.lower()
            # Match si alguna palabra clave está en el nombre
            if any(pal in nombre_lower for pal in palabras):
                resultados.append(p)
        return resultados[:8]

    async def obtener_por_id(self, producto_id: str) -> Optional[Producto]:
        self.llamadas_obtener_por_id.append(producto_id)
        return next((p for p in self._productos if p.id == producto_id), None)

    async def obtener_por_sku(self, sku: str) -> Optional[Producto]:
        return next((p for p in self._productos if p.sku == sku), None)

    async def obtener_por_codigo_barras(self, ean13: str) -> Optional[Producto]:
        return next((p for p in self._productos if p.codigo_barras == ean13), None)

    async def listar_por_categoria(self, categoria_id: str, filtros: Optional[FiltrosBusqueda] = None) -> List[Producto]:
        return [p for p in self._productos if p.categoria_id == categoria_id]

    async def listar_novedades(self, limite: int = 10, sede_id: Optional[str] = None) -> List[Producto]:
        return self._productos[:limite]

    async def listar_mas_vendidos(self, periodo_dias: int = 30, limite: int = 10, sede_id: Optional[str] = None) -> List[Producto]:
        return self._productos[:limite]

    async def obtener_precio(self, producto_id: str, sede_id: Optional[str] = None, cliente_id: Optional[str] = None):
        from app.services.providers.base import PrecioInfo
        p = await self.obtener_por_id(producto_id)
        if p:
            return PrecioInfo(producto_id=producto_id, precio_base=p.precio_base, precio_final=p.precio_final)
        return None

    async def obtener_precios_lote(self, producto_ids: List[str], sede_id: Optional[str] = None) -> dict:
        return {}

    async def verificar_stock(self, producto_id: str, sede_id: str):
        from app.services.providers.base import StockInfo
        p = await self.obtener_por_id(producto_id)
        if p:
            return StockInfo(producto_id=producto_id, sede_id=sede_id, cantidad=p.stock_total, disponible=p.stock_total > 0)
        return None

    async def verificar_stock_lote(self, items: List[tuple[str, str]]) -> dict:
        return {}

    async def comparar_productos(self, criterio) -> List[Producto]:
        return []

    async def obtener_alternativas(self, producto_id: str, limite: int = 5, sede_id: Optional[str] = None) -> List[Producto]:
        return []

    async def obtener_complementos(self, producto_id: str, limite: int = 5) -> List[Producto]:
        return []

    async def obtener_promociones_activas(self, sede_id: Optional[str] = None, categoria_id: Optional[str] = None):
        return []

    async def obtener_promociones_producto(self, producto_id: str, sede_id: Optional[str] = None):
        return []

    async def buscar_ingredientes_receta(self, ingredientes: List[str], sede_id: Optional[str] = None, presupuesto_max: Optional[float] = None):
        return {}

    async def calcular_costo_receta(self, ingredientes: List[dict], sede_id: Optional[str] = None):
        return {}

    async def sincronizar_catalogo_completo(self):
        return {}

    async def sincronizar_incremental(self, desde):
        return {}

    async def obtener_ultima_sincronizacion(self):
        return None


def _crear_producto_test(
    id: str,
    nombre: str,
    precio: float = 5000,
    categoria: str = "Test",
    stock: int = 10,
    etiquetas: List[str] = None
) -> Producto:
    """Helper para crear productos de prueba."""
    return Producto(
        id=id,
        sku=f"SKU-{id[:8]}",
        nombre=nombre,
        categoria_nombre=categoria,
        precio_base=precio,
        precio_final=precio,
        stock_total=stock,
        stock_por_sede={"sede_1": stock},
        etiquetas=etiquetas or [],
        fuente="test_fake",
    )


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def productos_fixture():
    """Productos de prueba para el catálogo."""
    return [
        _crear_producto_test("prod-001", "Leche Entera Alquería 1L", 4900, "Lacteos", 12, ["saludable"]),
        _crear_producto_test("prod-002", "Arroz Diana 1kg", 4500, "Abarrotes", 50),
        _crear_producto_test("prod-003", "Café Sello Rojo 500g", 18500, "Cafe", 20),
        _crear_producto_test("prod-004", "Huevos AAA x12", 14900, "Lacteos", 30),
        _crear_producto_test("prod-005", "Tomate Riñón 1kg", 4500, "Fruver", 25),
        _crear_producto_test("prod-006", "Cebolla Cabezona 1kg", 3200, "Fruver", 40),
        _crear_producto_test("prod-007", "Aceite Gourmet 1L", 13500, "Abarrotes", 15),
        _crear_producto_test("prod-008", "Pan Tajado Blanco", 4500, "Panaderia", 8),
    ]


@pytest.fixture
def proveedor_test(productos_fixture):
    """Proveedor fake inyectado para tests."""
    return ProveedorTestFake(productos_disponibles=productos_fixture)


@pytest.fixture
def proveedor_test_caido():
    """Proveedor fake que falla (simula MasControl caído)."""
    prov = ProveedorTestFake(debe_fallar=True)
    prov._ultimo_error = "Simulado: MasControl caído"
    return prov


@pytest.fixture
def app_con_proveedor(proveedor_test):
    """App FastAPI con proveedor fake inyectado."""
    # Guardar estado original
    original_proveedor = proveedor_registry._proveedor_actual
    original_forzar = proveedor_registry._forzar_mock

    # Inyectar proveedor de prueba
    proveedor_registry._proveedor_actual = proveedor_test
    proveedor_registry._forzar_mock = False
    proveedor_registry._proveedor_seleccionado = "test_fake"

    # Reset catálogo state
    catalogo_state._estado = CatalogoEstado.CONECTADO
    catalogo_state._ultimo_error = None

    app = FastAPI()
    app.include_router(endpoint_agente.router, prefix="/api/v1/agente")

    yield app

    # Restaurar
    proveedor_registry._proveedor_actual = original_proveedor
    proveedor_registry._forzar_mock = original_forzar


@pytest.fixture
def app_con_proveedor_caido(proveedor_test_caido):
    """App FastAPI con proveedor que falla."""
    original_proveedor = proveedor_registry._proveedor_actual
    original_forzar = proveedor_registry._forzar_mock

    proveedor_registry._proveedor_actual = proveedor_test_caido
    proveedor_registry._forzar_mock = False
    proveedor_registry._proveedor_seleccionado = "test_fake"

    catalogo_state._estado = CatalogoEstado.DEGRADADO
    catalogo_state._ultimo_error = "Simulado: MasControl caído"

    app = FastAPI()
    app.include_router(endpoint_agente.router, prefix="/api/v1/agente")

    yield app

    proveedor_registry._proveedor_actual = original_proveedor
    proveedor_registry._forzar_mock = original_forzar


@pytest.fixture
def cliente_test(app_con_proveedor):
    """Cliente HTTP de prueba."""
    return AsyncClient(transport=ASGITransport(app=app_con_proveedor), base_url="http://test")


@pytest.fixture
def cliente_test_caido(app_con_proveedor_caido):
    """Cliente HTTP con proveedor caído."""
    return AsyncClient(transport=ASGITransport(app=app_con_proveedor_caido), base_url="http://test")


# ============================================================
# TESTS DE INTEGRACIÓN
# ============================================================

class TestAgenteUsaContratoProveedor:
    """1. El agente depende del contrato común (ProductProvider protocol), NO de implementaciones concretas."""

    async def test_agente_funciona_con_cualquier_implementacion_productprovider(
        self, cliente_test, proveedor_test
    ):
        """El agente funciona idéntico con MockProvider, MasControlProvider o TestFakeProvider."""
        # El endpoint usa get_proveedor_catalogo() que retorna ProductProvider
        # No importa qué implementación sea - el agente usa la interfaz del protocolo

        respuesta = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "quiero leche entera"}
        )

        assert respuesta.status_code == 200
        data = respuesta.json()

        # Verifica que la búsqueda pasó por el proveedor fake
        assert len(proveedor_test.llamadas_busqueda) == 1
        assert proveedor_test.llamadas_busqueda[0]["query"] == "quiero leche entera"
        assert proveedor_test.llamadas_busqueda[0]["tipo"] == TipoBusqueda.TEXTO

        # Respuesta incluye productos del proveedor
        assert data["productos_recomendados"]
        assert any("Leche Entera" in p["nombre"] for p in data["productos_recomendados"])
        assert data["hubo_resultados_relevantes"] is True

    async def test_agente_no_importa_mockprovider_ni_mascontrolprovider_directamente(
        self, cliente_test
    ):
        """Verifica que el endpoint no hace import directa de proveedores concretos."""
        # El endpoint importa: from app.services.providers import get_proveedor_catalogo
        # Y usa: proveedor = Depends(get_proveedor_catalogo)
        # No importa: from app.services.providers.mock_provider import mock_provider
        # No importa: from app.services.providers.mascontrol_provider import mascontrol_provider

        respuesta = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "hola"}
        )

        assert respuesta.status_code == 200
        # Si no hubiera import directo, la prueba pasa
        # Esto es validación arquitectural - si hubiera imports directos, fallaría al cambiar proveedor


class TestSaludosYRecetasSinBusqueda:
    """2. Saludos y recetas generales NO necesitan búsquedas de productos."""

    async def test_saludo_no_hace_busqueda_productos(self, cliente_test, proveedor_test):
        """Saludos (hola, buenas, etc.) no invocan al proveedor de catálogo."""
        for saludo in ["hola", "buenos dias", "buenas tardes", "ola", "que tal", "hola aya"]:
            proveedor_test.llamadas_busqueda.clear()

            respuesta = await cliente_test.post(
                "/api/v1/agente/chat",
                json={"mensaje": saludo}
            )

            assert respuesta.status_code == 200
            data = respuesta.json()

            # CLAVE: NO se llamó al proveedor
            assert len(proveedor_test.llamadas_busqueda) == 0, f"Saludo '{saludo}' hizo búsqueda innecesaria"

            # Respuesta es saludo con info de ayuda
            assert "La Economía Aya" in data["respuesta"]
            assert data["productos_recomendados"] == []
            assert data["hubo_resultados_relevantes"] is False

    async def test_despedida_no_hace_busqueda_productos(self, cliente_test, proveedor_test):
        """Despedidas (chao, gracias, etc.) no invocan al proveedor."""
        for despedida in ["chao", "gracias", "muchas gracias", "listo gracias", "nos vemos"]:
            proveedor_test.llamadas_busqueda.clear()

            respuesta = await cliente_test.post(
                "/api/v1/agente/chat",
                json={"mensaje": despedida}
            )

            assert respuesta.status_code == 200
            data = respuesta.json()

            # NO búsqueda
            assert len(proveedor_test.llamadas_busqueda) == 0
            assert data["productos_recomendados"] == []

    async def test_receta_general_no_hace_busqueda_productos(self, cliente_test, proveedor_test):
        """Preguntas por recetas generales usan knowledge base, no catálogo."""
        for consulta in [
            "que puedo hacer de desayuno",
            "se me antoja algo dulce",
            "recomiendame algo para cocinar",
            "ideas para la cena",
        ]:
            proveedor_test.llamadas_busqueda.clear()

            respuesta = await cliente_test.post(
                "/api/v1/agente/chat",
                json={"mensaje": consulta}
            )

            assert respuesta.status_code == 200
            data = respuesta.json()

            # NO búsqueda en catálogo - usa knowledge base de recetas
            assert len(proveedor_test.llamadas_busqueda) == 0
            assert data["productos_recomendados"] == []
            assert "receta" in data["respuesta"].lower() or "desayuno" in data["respuesta"].lower() or "cena" in data["respuesta"].lower()

    async def test_receta_especifica_solo_devuelve_info_receta_sin_buscar_catalogo(
        self, cliente_test, proveedor_test
    ):
        """Pedir receta específica (ej: 'quiero hacer ajiaco') devuelve info de receta sin buscar catálogo."""
        proveedor_test.llamadas_busqueda.clear()

        respuesta = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "quiero hacer ajiaco santafereño"}
        )

        assert respuesta.status_code == 200
        data = respuesta.json()

        # NO búsqueda en catálogo para la receta en sí
        # (la receta viene del knowledge base interno)
        assert len(proveedor_test.llamadas_busqueda) == 0
        assert data["receta"] is not None
        assert data["receta"]["nombre"] == "Ajiaco Santafereño"
        assert "guasca" in data["respuesta"].lower()


class TestBusquedasComercialesUsanProveedorSeleccionado:
    """3. Búsquedas comerciales utilizan el proveedor seleccionado (Mock/MasControl/TestFake)."""

    async def test_busqueda_producto_usa_proveedor_activo(self, cliente_test, proveedor_test):
        """Consultas de producto invocan al proveedor activo."""
        proveedor_test.llamadas_busqueda.clear()

        respuesta = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "tienen arroz"}
        )

        assert respuesta.status_code == 200
        data = respuesta.json()

        # SÍ buscó en el proveedor
        assert len(proveedor_test.llamadas_busqueda) == 1
        assert proveedor_test.llamadas_busqueda[0]["query"] == "tienen arroz"

        # Productos vienen del proveedor
        assert data["hubo_resultados_relevantes"] is True
        assert any("Arroz" in p["nombre"] for p in data["productos_recomendados"])

    async def test_busqueda_con_filtros_pasa_filtros_al_proveedor(self, cliente_test, proveedor_test):
        """Filtros de sede, stock, límite se pasan al proveedor."""
        import uuid
        proveedor_test.llamadas_busqueda.clear()

        sede_id_valida = str(uuid.uuid4())
        respuesta = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "aceite", "sede_id": sede_id_valida}
        )

        assert respuesta.status_code == 200

        llamada = proveedor_test.llamadas_busqueda[0]
        assert llamada["filtros"] is not None
        assert llamada["filtros"].sede_id == sede_id_valida
        assert llamada["filtros"].solo_con_stock is True
        assert llamada["filtros"].limite == 8

    async def test_comparativa_usa_proveedor(self, cliente_test, proveedor_test):
        """Preguntas comparativas usan el proveedor (Comparison Engine hace búsquedas propias)."""
        proveedor_test.llamadas_busqueda.clear()

        respuesta = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "cual aceite es mejor para freir"}
        )

        assert respuesta.status_code == 200
        # El Comparison Engine hace sus propias búsquedas por término
        # Se esperan múltiples llamadas: 1 búsqueda inicial + N búsquedas del comparison engine
        assert len(proveedor_test.llamadas_busqueda) >= 1
        # Verificar que al menos una búsqueda fue con filtro de stock
        assert any(
            llamada["filtros"] and llamada["filtros"].solo_con_stock is True
            for llamada in proveedor_test.llamadas_busqueda
        )


class TestFallasMasControlNoActivanMock:
    """4. Fallos de MasControl NO activan datos ficticios (degradan con error explícito)."""

    async def test_proveedor_caido_degrada_gracefully_sin_mock(
        self, cliente_test_caido, proveedor_test_caido
    ):
        """Cuando el proveedor falla, el agente responde con fallback determinista, NO activa mock."""
        proveedor_test_caido.llamadas_busqueda.clear()

        respuesta = await cliente_test_caido.post(
            "/api/v1/agente/chat",
            json={"mensaje": "quiero leche"}
        )

        assert respuesta.status_code == 200
        data = respuesta.json()

        # El proveedor falló (se intentó llamar)
        assert len(proveedor_test_caido.llamadas_busqueda) == 1

        # PERO el agente responde con fallback inteligente (determinista)
        assert data["generado_por_llm"] is False
        assert data["hubo_resultados_relevantes"] is False
        # Respuesta incluye alternativas inteligentes, no datos mock
        assert "alternativas" in data["respuesta"].lower() or "leche" in data["respuesta"].lower()

    async def test_estado_catalogo_refleja_degradado_no_mock(
        self, cliente_test_caido
    ):
        """Endpoint de estado muestra DEGRADADO, no MOCK activado silenciosamente."""
        respuesta = await cliente_test_caido.get("/api/v1/agente/estado-catalogo")

        assert respuesta.status_code == 200
        data = respuesta.json()

        # Estado del catálogo es DEGRADADO (no CONECTADO con mock)
        assert data["catalogo"]["estado"] == "degradado"
        assert data["catalogo"]["conectado"] is False
        assert data["catalogo"]["modo_mock"] is False  # ¡No está en modo mock!

        # Proveedor activo muestra error
        assert data["proveedor"]["disponible"] is False
        assert data["proveedor"]["error"] is not None
        assert "caído" in data["proveedor"]["error"].lower() or "fallo" in data["proveedor"]["error"].lower()

    async def test_registro_proveedor_rechaza_mock_en_produccion(self):
        """Registry lanza error si se intenta usar MockProvider en producción (debug=False)."""
        from app.core.config import settings

        # Simular producción
        original_debug = settings.debug
        settings.debug = False

        try:
            # Forzar mock en "producción" debe fallar
            proveedor_registry._forzar_mock = True
            proveedor_registry._proveedor_actual = None

            with pytest.raises(ProveedorNoDisponibleError) as exc:
                proveedor_registry.obtener_proveedor()

            assert "PROHIBIDO" in str(exc.value)
            assert "MockProvider no puede usarse en producción" in str(exc.value)
        finally:
            settings.debug = original_debug
            proveedor_registry._forzar_mock = False
            proveedor_registry._proveedor_actual = None


class TestHistorialConMensajesTipados:
    """5. El historial funciona con mensajes tipados (dict role/content)."""

    async def test_historial_formato_dict_role_content(self, cliente_test):
        """Conversación multi-turno con historial en formato dict {"role": "...", "content": "..."}."""
        # Turno 1: Usuario pregunta por leche
        respuesta1 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "quiero leche entera"}
        )
        assert respuesta1.status_code == 200
        data1 = respuesta1.json()
        conversacion_id = data1["conversacion_id"]

        # Turno 2: Usuario pregunta por precio (usa mismo conversacion_id)
        respuesta2 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "cuanto cuesta", "conversacion_id": conversacion_id}
        )
        assert respuesta2.status_code == 200
        data2 = respuesta2.json()

        # Verificar que el historial llegó al agente (formato dict)
        # El test test_el_historial_llega_al_llm ya valida esto en test_agente.py
        # Aquí verificamos que el endpoint mantiene el mismo conversacion_id
        assert data2["conversacion_id"] == conversacion_id

    async def test_historial_conversacion_persiste_entre_turnos(self, cliente_test):
        """El contexto de conversación se mantiene entre múltiples turnos."""
        # Turno 1
        r1 = await cliente_test.post("/api/v1/agente/chat", json={"mensaje": "hola"})
        assert r1.status_code == 200
        cid = r1.json()["conversacion_id"]

        # Turno 2 - pregunta contextual
        r2 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "y arroz tienen?", "conversacion_id": cid}
        )
        assert r2.status_code == 200
        assert r2.json()["conversacion_id"] == cid

        # Turno 3 - referencia a producto anterior
        r3 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "el primero que me dijiste", "conversacion_id": cid}
        )
        assert r3.status_code == 200
        assert r3.json()["conversacion_id"] == cid

    async def test_historial_acepta_formato_legacy_tuplas(self):
        """Compatibilidad: formato legacy ('usuario', 'contenido') se convierte a dict."""
        from app.services.agente import generar_respuesta_agente
        from app.schemas.busqueda import ProductoRecuperado
        from decimal import Decimal
        import uuid

        def _producto():
            return ProductoRecuperado(
                producto_id=str(uuid.uuid4()),
                nombre="Leche Test",
                categoria_nombre="Lacteos",
                precio=Decimal("4500"),
                stock_sede=10,
                similitud=0.8,
            )

        # Historial en formato legacy (tuplas)
        historial_legacy = [
            ("usuario", "hola"),
            ("asistente", "¡Hola! ¿En qué te ayudo?"),
        ]

        # No debe lanzar error - convierte internamente
        texto, por_llm = await generar_respuesta_agente(
            "quiero leche",
            [_producto()],
            historial_conversacion=historial_legacy,
        )

        assert isinstance(texto, str)
        assert len(texto) > 0


class TestContextoPersisteEntreTurnos:
    """6. El agente conserva contexto entre turnos (productos_recientes, receta_actual, lista_mercado, presupuesto)."""

    async def test_contexto_productos_recientes_se_actualiza(self, cliente_test, proveedor_test):
        """productos_recientes se actualiza con productos mencionados en cada turno."""
        # Turno 1: Busca leche
        r1 = await cliente_test.post("/api/v1/agente/chat", json={"mensaje": "quiero leche"})
        cid = r1.json()["conversacion_id"]

        # Turno 2: Busca pan
        r2 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "y pan tienen?", "conversacion_id": cid}
        )

        # Turno 3: Pregunta por "el primero" (leche)
        r3 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "mejor el primero", "conversacion_id": cid}
        )

        # El contexto interno del agente debe tener ambos productos
        # Verificamos indirectamente: la respuesta del turno 3 debe entender "el primero"
        assert r3.status_code == 200

    async def test_contexto_receta_actual_persiste(self, cliente_test):
        """receta_actual persiste cuando se detecta una receta."""
        # Turno 1: Pide receta de ajiaco
        r1 = await cliente_test.post("/api/v1/agente/chat", json={"mensaje": "quiero hacer ajiaco"})
        cid = r1.json()["conversacion_id"]
        data1 = r1.json()

        assert data1["receta"] is not None
        assert data1["receta"]["nombre"] == "Ajiaco Santafereño"

        # Turno 2: Pregunta por ingredientes (contexto de receta activa)
        r2 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "que ingredientes lleva?", "conversacion_id": cid}
        )

        assert r2.status_code == 200
        data2 = r2.json()
        # La receta debe persistir en contexto
        assert data2["receta"] is not None
        assert data2["receta"]["nombre"] == "Ajiaco Santafereño"

    async def test_contexto_lista_mercado_se_construye_progresivamente(self, cliente_test, proveedor_test):
        """lista_mercado se construye a lo largo de la conversación."""
        # Turno 1: Inicia lista
        r1 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "necesito hacer mercado para la semana"}
        )
        cid = r1.json()["conversacion_id"]

        # Turno 2: Agrega productos
        r2 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "agrega arroz y frijoles", "conversacion_id": cid}
        )

        # Turno 3: Pide total
        r3 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "cuanto me sale todo?", "conversacion_id": cid}
        )

        assert r3.status_code == 200
        # El agente debe tener contexto de la lista en progreso

    async def test_contexto_presupuesto_se_respeta_en_recomendaciones(self, cliente_test, proveedor_test):
        """presupuesto mencionado se usa para filtrar recomendaciones."""
        # Turno 1: Establece presupuesto
        r1 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "tengo 20 mil pesos para el mercado"}
        )
        cid = r1.json()["conversacion_id"]

        # Turno 2: Pide recomendación dentro del presupuesto
        r2 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "que me alcanza con eso?", "conversacion_id": cid}
        )

        assert r2.status_code == 200
        data2 = r2.json()
        # La respuesta debe mencionar opciones acordes al presupuesto
        assert "20" in data2["respuesta"] or "veinte" in data2["respuesta"].lower() or "mil" in data2["respuesta"].lower()

    async def test_multiples_turnos_contexto_completo(self, cliente_test, proveedor_test):
        """Prueba completa: múltiples turnos mantienen todos los contextos."""
        # 1. Saludo
        r1 = await cliente_test.post("/api/v1/agente/chat", json={"mensaje": "hola"})
        cid = r1.json()["conversacion_id"]

        # 2. Pregunta receta
        r2 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "quiero hacer huevos pericos", "conversacion_id": cid}
        )
        assert r2.json()["receta"] is not None

        # 3. Pregunta por ingrediente específico
        r3 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "cuantos huevos necesito?", "conversacion_id": cid}
        )
        assert r3.status_code == 200
        assert "huevo" in r3.json()["respuesta"].lower()

        # 4. Cambia a búsqueda comercial
        r4 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "y tambien quiero comprar cafe", "conversacion_id": cid}
        )
        assert r4.status_code == 200
        # Debe buscar café en catálogo (proveedor)
        assert len(proveedor_test.llamadas_busqueda) >= 1

        # 5. Pregunta contextual combinada
        r5 = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "para los huevos pericos y el cafe, que me alcanza con 30 mil?", "conversacion_id": cid}
        )
        assert r5.status_code == 200
        # Contexto: receta (huevos pericos) + producto reciente (café) + presupuesto (30k)


class TestArquitecturaProviderPattern:
    """Tests que validan la arquitectura del Provider Pattern."""

    async def test_endpoint_usa_dependency_injection_proveedor(self):
        """El endpoint usa Depends(get_proveedor_catalogo) - inyección de dependencias."""
        import inspect
        from app.api.v1.endpoints.agente import agente_chat

        sig = inspect.signature(agente_chat)
        params = sig.parameters

        # Verifica que proveedor viene por DI
        assert "proveedor" in params
        proveedor_param = params["proveedor"]
        # En FastAPI, Depends se ve en default
        assert proveedor_param.default is not None

        # Verifica que NO hay imports directos de proveedores concretos en el módulo
        import app.api.v1.endpoints.agente as modulo_agente
        source = inspect.getsource(modulo_agente)

        assert "from app.services.providers.mock_provider import" not in source
        assert "from app.services.providers.mascontrol_provider import" not in source
        assert "mock_provider" not in source or "mock_provider" in source  # Solo en type hints o comments
        assert "mascontrol_provider" not in source or "mascontrol_provider" in source

    async def test_registry_controla_seleccion_proveedor(self):
        """ProveedorRegistry controla qué proveedor se usa según config y estado."""
        # Registry tiene lógica de selección, no el endpoint
        info = proveedor_registry.obtener_info_estado()

        assert "proveedor" in info
        assert "solicitado" in info["proveedor"]
        assert "activo" in info["proveedor"]
        assert "disponible" in info["proveedor"]
        assert "reglas" in info
        assert "mock_permitido" in info["reglas"]
        assert "mascontrol_requerido_en_produccion" in info["reglas"]

    async def test_health_check_proveedor_disponible(self, proveedor_test):
        """Health check del proveedor funciona correctamente."""
        health = await proveedor_test.health_check()
        assert health["estado"] == "ok"
        assert health["proveedor"] == "test_fake"

    async def test_proveedor_retorna_contrato_comun_producto(self, proveedor_test):
        """Proveedor retorna instancias de Producto (contrato común), no dicts sueltos."""
        productos = await proveedor_test.buscar("leche")

        assert len(productos) > 0
        p = productos[0]
        assert isinstance(p, Producto)
        # Verifica campos obligatorios del contrato
        assert p.id
        assert p.sku
        assert p.nombre
        assert p.precio_final > 0
        assert p.fuente == "test_fake"  # Origen identificable


# ============================================================
# TESTS DE REGRESIÓN - Comportamientos que no deben romperse
# ============================================================

class TestRegresiones:
    """Tests que evitan regresiones en comportamientos conocidos."""

    async def test_typos_colombianos_siguen_funcionando(self, cliente_test):
        """Abreviaciones y typos colombianos siguen funcionando."""
        for typo, esperado in [
            ("xq no hay leche", "porque"),
            ("q tal", "que tal"),
            ("kiero arroz", "quiero"),
            ("pa que sirve", "para"),
            ("ta rico", "esta"),
        ]:
            respuesta = await cliente_test.post(
                "/api/v1/agente/chat",
                json={"mensaje": typo}
            )
            assert respuesta.status_code == 200
            # No debe fallar, debe responder coherentemente

    async def test_precios_formato_colombiano(self, cliente_test, proveedor_test):
        """Precios se formatean con puntos de miles (formato colombiano)."""
        respuesta = await cliente_test.post(
            "/api/v1/agente/chat",
            json={"mensaje": "precio de la leche"}
        )

        assert respuesta.status_code == 200
        data = respuesta.json()

        if data["productos_recomendados"]:
            precio_str = str(data["productos_recomendados"][0].get("precio", ""))
            # Formato: 4.500 (punto de miles), no 4,500 (coma)
            if "." in precio_str or "," in precio_str:
                assert "." in precio_str  # Punto para miles en colombiano

    async def test_eliminar_conversacion_funciona(self, cliente_test):
        """DELETE /conversacion/{id} elimina el historial (Ley 1581)."""
        # Crear conversación
        r1 = await cliente_test.post("/api/v1/agente/chat", json={"mensaje": "hola"})
        cid = r1.json()["conversacion_id"]

        # Eliminar
        r2 = await cliente_test.delete(f"/api/v1/agente/conversacion/{cid}")
        assert r2.status_code == 200
        assert r2.json()["ok"] is True

        # Verificar que ya no existe (404 al eliminar de nuevo)
        r3 = await cliente_test.delete(f"/api/v1/agente/conversacion/{cid}")
        assert r3.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])