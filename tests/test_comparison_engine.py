"""
Tests para el Comparison Engine.

Cubre 14+ escenarios:
1. Comparación básica precio por unidad (kg vs g)
2. Comparación con unidades incompatibles (g vs ml)
3. Comparación sede-aware
4. Comparación con promociones mixtas
5. Comparación con productos sin stock
6. Comparación con presentación ambigua
7. Comparación tipo "completa" con contexto
8. Comparación por precio total
9. Comparación por cantidad
10. Comparación por disponibilidad
11. Comparación de productos seleccionados por SKU
12. Formateo para agente
13. Unidades: docena, pack, litros
14. Edge cases: precios iguales, un solo producto
"""
import pytest
import pytest_asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional

from app.services.comparison_engine import ComparisonEngine, ProductoAnalisis, EstadoComparacion
from app.schemas.comparison import (
    TipoComparacion,
    ProductoComparacion,
    ResultadoComparacionItem,
    ComparacionResponse,
    SolicitudComparacion,
    normalizar_unidad,
    convertir_a_base,
    son_unidades_compatibles,
    UnidadMedida,
)
from app.services.providers.base import (
    Producto, ProductProvider, FiltrosBusqueda, TipoBusqueda, PrecioInfo, StockInfo
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_proveedor():
    """Proveedor mock con datos de prueba realistas."""
    proveedor = AsyncMock(spec=ProductProvider)

    # Productos de prueba
    productos = [
        Producto(
            id="1",
            sku="ACEITE-001",
            nombre="Aceite de Girasol",
            marca="Nutrioli",
            presentacion="Botella 900ml",
            categoria_id="aceites",
            categoria_nombre="Aceites",
            unidad_medida="ml",
            contenido_neto=900,
            stock_por_sede={"SEDE-001": 50},
            fuente="fixture_desarrollo"
        ),
        Producto(
            id="2",
            sku="ACEITE-002",
            nombre="Aceite de Girasol",
            marca="Gourmet",
            presentacion="Botella 1.8L",
            categoria_id="aceites",
            categoria_nombre="Aceites",
            unidad_medida="l",
            contenido_neto=1.8,
            stock_por_sede={"SEDE-001": 30},
            fuente="fixture_desarrollo"
        ),
        Producto(
            id="3",
            sku="ARROZ-001",
            nombre="Arroz Blanco",
            marca="Roa",
            presentacion="Bolsa 1kg",
            categoria_id="granos",
            categoria_nombre="Granos",
            unidad_medida="kg",
            contenido_neto=1,
            stock_por_sede={"SEDE-001": 100},
            fuente="fixture_desarrollo"
        ),
        Producto(
            id="4",
            sku="ARROZ-002",
            nombre="Arroz Blanco",
            marca="Diana",
            presentacion="Bolsa 500g",
            categoria_id="granos",
            categoria_nombre="Granos",
            unidad_medida="g",
            contenido_neto=500,
            stock_por_sede={"SEDE-001": 80},
            fuente="fixture_desarrollo"
        ),
        Producto(
            id="5",
            sku="LECHE-001",
            nombre="Leche Entera",
            marca="Alpina",
            presentacion="Bolsa 1L",
            categoria_id="lacteos",
            categoria_nombre="Lácteos",
            unidad_medida="l",
            contenido_neto=1,
            stock_por_sede={"SEDE-001": 200},
            fuente="fixture_desarrollo"
        ),
        Producto(
            id="6",
            sku="HUEVOS-001",
            nombre="Huevos AA",
            marca="Kikes",
            presentacion="Caja x 12 und",
            categoria_id="huevos",
            categoria_nombre="Huevos",
            unidad_medida="und",
            contenido_neto=12,
            stock_por_sede={"SEDE-001": 0},  # Sin stock
            fuente="fixture_desarrollo"
        ),
        Producto(
            id="7",
            sku="ACEITE-OLIVA-001",
            nombre="Aceite de Oliva Extra Virgen",
            marca="La Española",
            presentacion="Botella 500ml",
            categoria_id="aceites",
            categoria_nombre="Aceites",
            unidad_medida="ml",
            contenido_neto=500,
            stock_por_sede={"SEDE-001": 15},
            fuente="fixture_desarrollo"
        ),
    ]

    # Precios por ID de producto (obtener_precios_lote usa producto_ids)
    precios = {
        "1": PrecioInfo(producto_id="1", sede_id="SEDE-001", precio_base=15000, precio_final=12000, tiene_promocion=True, promocion_descripcion="20% dto"),
        "2": PrecioInfo(producto_id="2", sede_id="SEDE-001", precio_base=22000, precio_final=22000),
        "3": PrecioInfo(producto_id="3", sede_id="SEDE-001", precio_base=4500, precio_final=4500),
        "4": PrecioInfo(producto_id="4", sede_id="SEDE-001", precio_base=2500, precio_final=2500),
        "5": PrecioInfo(producto_id="5", sede_id="SEDE-001", precio_base=4800, precio_final=4800),
        "6": PrecioInfo(producto_id="6", sede_id="SEDE-001", precio_base=12000, precio_final=12000),
        "7": PrecioInfo(producto_id="7", sede_id="SEDE-001", precio_base=35000, precio_final=35000),
    }

    # Stock por ID de producto
    stock_data = {
        "1": 50,
        "2": 30,
        "3": 100,
        "4": 80,
        "5": 200,
        "6": 0,  # Sin stock
        "7": 15,
    }

    # Mock para buscar (usa query y filtros)
    async def buscar(query: str, filtros: Optional[FiltrosBusqueda] = None, tipo_busqueda: TipoBusqueda = TipoBusqueda.TEXTO) -> List[Producto]:
        query_lower = query.lower()
        resultados = []
        for p in productos:
            if (query_lower in p.nombre.lower() or
                query_lower in (p.marca or "").lower() or
                query_lower in p.sku.lower() or
                query_lower in (p.presentacion or "").lower()):
                resultados.append(p)
        if filtros and filtros.limite:
            resultados = resultados[:filtros.limite]
        return resultados

    # Mock para obtener_por_sku
    async def obtener_por_sku(sku: str) -> Optional[Producto]:
        for p in productos:
            if p.sku == sku:
                return p
        return None

    # Mock para obtener_precios_lote (usa producto_ids)
    async def obtener_precios_lote(producto_ids: List[str], sede_id: Optional[str] = None) -> Dict[str, PrecioInfo]:
        return {pid: precios.get(pid, PrecioInfo(producto_id=pid, precio_final=0)) for pid in producto_ids}

    # Mock para verificar_stock_lote (usa List[tuple[producto_id, sede_id]])
    async def verificar_stock_lote(items: List[tuple[str, str]]) -> Dict[str, StockInfo]:
        result = {}
        for producto_id, sid in items:
            cant = stock_data.get(producto_id, 0)
            result[producto_id] = StockInfo(
                producto_id=producto_id,
                sede_id=sid,
                cantidad=cant,
                disponible=cant > 0
            )
        return result

    proveedor.buscar = buscar
    proveedor.obtener_por_sku = obtener_por_sku
    proveedor.obtener_precios_lote = obtener_precios_lote
    proveedor.verificar_stock_lote = verificar_stock_lote

    return proveedor


@pytest.fixture
def comparison_engine(mock_proveedor):
    """Instancia del Comparison Engine con proveedor mock."""
    return ComparisonEngine(mock_proveedor)


# ============================================================
# TESTS DE UTILIDADES DE UNIDADES
# ============================================================

class TestUnidadesUtilidades:
    """Tests para funciones de normalización y conversión de unidades."""

    def test_normalizar_unidad_masa(self):
        assert normalizar_unidad("g") == UnidadMedida.GRAMO
        assert normalizar_unidad("gr") == UnidadMedida.GRAMO
        assert normalizar_unidad("gramo") == UnidadMedida.GRAMO
        assert normalizar_unidad("kg") == UnidadMedida.KILOGRAMO
        assert normalizar_unidad("kilo") == UnidadMedida.KILOGRAMO
        assert normalizar_unidad("KILOGRAMO") == UnidadMedida.KILOGRAMO

    def test_normalizar_unidad_volumen(self):
        assert normalizar_unidad("ml") == UnidadMedida.MILILITRO
        assert normalizar_unidad("l") == UnidadMedida.LITRO
        assert normalizar_unidad("lt") == UnidadMedida.LITRO
        assert normalizar_unidad("litro") == UnidadMedida.LITRO

    def test_normalizar_unidad_cuenta(self):
        assert normalizar_unidad("und") == UnidadMedida.UNIDAD
        assert normalizar_unidad("unidad") == UnidadMedida.UNIDAD
        assert normalizar_unidad("pack") == UnidadMedida.PAQUETE
        assert normalizar_unidad("docena") == UnidadMedida.DOCINA
        assert normalizar_unidad("doc") == UnidadMedida.DOCINA

    def test_normalizar_unidad_desconocida(self):
        assert normalizar_unidad("xyz") is None
        assert normalizar_unidad("") is None

    def test_convertir_a_base_masa(self):
        assert convertir_a_base(Decimal("1"), "kg") == Decimal("1000")
        assert convertir_a_base(Decimal("500"), "g") == Decimal("500")
        assert convertir_a_base(Decimal("1.5"), "kg") == Decimal("1500")

    def test_convertir_a_base_volumen(self):
        assert convertir_a_base(Decimal("1"), "l") == Decimal("1000")
        assert convertir_a_base(Decimal("900"), "ml") == Decimal("900")
        assert convertir_a_base(Decimal("1.8"), "l") == Decimal("1800")

    def test_convertir_a_base_cuenta(self):
        # 1 docena = 12 unidades
        assert convertir_a_base(Decimal("1"), "doc") == Decimal("12")
        assert convertir_a_base(Decimal("1"), "docena") == Decimal("12")
        # 6 packs = 6 unidades (pack factor = 1)
        assert convertir_a_base(Decimal("6"), "pack") == Decimal("6")
        # 12 unidades = 12
        assert convertir_a_base(Decimal("12"), "und") == Decimal("12")

    def test_son_unidades_compatibles_masa(self):
        assert son_unidades_compatibles("g", "kg") is True
        assert son_unidades_compatibles("kg", "gramos") is True

    def test_son_unidades_compatibles_volumen(self):
        assert son_unidades_compatibles("ml", "l") is True
        assert son_unidades_compatibles("litro", "mililitro") is True

    def test_son_unidades_compatibles_cuenta(self):
        assert son_unidades_compatibles("und", "pack") is True
        assert son_unidades_compatibles("docena", "unidad") is True

    def test_son_unidades_incompatibles(self):
        assert son_unidades_compatibles("g", "ml") is False  # masa vs volumen
        assert son_unidades_compatibles("kg", "l") is False
        assert son_unidades_compatibles("und", "g") is False
        assert son_unidades_compatibles("xyz", "g") is False


# ============================================================
# TESTS DE COMPARACIÓN BÁSICA
# ============================================================

class TestComparacionBasica:
    """Tests de comparación básica precio por unidad."""

    @pytest.mark.asyncio
    async def test_comparar_aceites_ml_vs_l(self, comparison_engine):
        """Test 1: Comparación precio por unidad - ml vs L (compatibles)."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["aceite girasol", "aceite"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.comparables is True
        assert len(resultado.productos) >= 2
        assert resultado.tipo_comparacion == TipoComparacion.PRECIO_POR_UNIDAD

        # Verificar precios por unidad base calculados
        # ACEITE-001: 12000 COP / 900ml = 13.33 COP/ml = 13333 COP/L
        # ACEITE-002: 22000 COP / 1800ml = 12.22 COP/ml = 12222 COP/L
        # El segundo debería ser mejor (menor precio por L)
        mejor = resultado.mejor_opcion
        assert mejor is not None
        assert mejor.sku == "ACEITE-002"  # Mejor precio por litro

    @pytest.mark.asyncio
    async def test_comparar_arroz_kg_vs_g(self, comparison_engine):
        """Test 2: Comparación arroz 1kg vs 500g."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["arroz blanco", "arroz"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.comparables is True
        assert len(resultado.productos) >= 2

        # ARROZ-001: 4500 COP / 1000g = 4.5 COP/g
        # ARROZ-002: 2500 COP / 500g = 5.0 COP/g
        # El primero es mejor
        mejor = resultado.mejor_opcion
        assert mejor.sku == "ARROZ-001"

    @pytest.mark.asyncio
    async def test_comparar_con_promocion(self, comparison_engine):
        """Test 3: Comparación con promociones mixtas."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["aceite girasol", "aceite"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        # ACEITE-001 tiene promoción (precio_base 15000 -> precio_final 12000)
        # ACEITE-002 sin promoción
        promo_items = [p for p in resultado.productos if p.producto.tiene_promocion]
        assert len(promo_items) == 1
        assert promo_items[0].producto.sku == "ACEITE-001"

        # La limitación debe mencionar promociones mixtas
        assert any("promoción" in lim.lower() for lim in resultado.limitaciones)


# ============================================================
# TESTS DE UNIDADES INCOMPATIBLES
# ============================================================

class TestUnidadesIncompatibles:
    """Tests para detección de unidades incompatibles."""

    @pytest.mark.asyncio
    async def test_comparar_g_vs_ml_diferente_densidad(self, comparison_engine):
        """Test 4: Comparación g vs ml (incompatibles - masa vs volumen)."""
        # Buscar "aceite" y "arroz" juntos - unidades incompatibles
        solicitud = SolicitudComparacion(
            terminos_busqueda=["aceite", "arroz"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        # Debería detectar incompatibilidad
        assert resultado.comparables is False
        assert any("distinta dimensión" in lim or "incompat" in lim.lower() for lim in resultado.limitaciones)

    @pytest.mark.asyncio
    async def test_comparar_und_vs_kg_incompatible(self, comparison_engine, mock_proveedor):
        """Test: Comparación unidades vs peso (incompatibles)."""
        # Temporalmente dar stock a huevos para que aparezca en resultados
        mock_proveedor.verificar_stock_lote = AsyncMock(return_value={
            "1": StockInfo(producto_id="1", sede_id="SEDE-001", cantidad=50, disponible=True),
            "2": StockInfo(producto_id="2", sede_id="SEDE-001", cantidad=30, disponible=True),
            "3": StockInfo(producto_id="3", sede_id="SEDE-001", cantidad=100, disponible=True),
            "4": StockInfo(producto_id="4", sede_id="SEDE-001", cantidad=80, disponible=True),
            "5": StockInfo(producto_id="5", sede_id="SEDE-001", cantidad=200, disponible=True),
            "6": StockInfo(producto_id="6", sede_id="SEDE-001", cantidad=10, disponible=True),  # Huevos con stock
            "7": StockInfo(producto_id="7", sede_id="SEDE-001", cantidad=15, disponible=True),
        })

        solicitud = SolicitudComparacion(
            terminos_busqueda=["huevos", "arroz"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        # Debería detectar incompatibilidad (und vs kg/g)
        assert resultado.comparables is False
        assert any("incompat" in lim.lower() or "distinta dimensión" in lim for lim in resultado.limitaciones)


# ============================================================
# TESTS SEDE-AWARE
# ============================================================

class TestSedeAware:
    """Tests de comparación consciente de sede."""

    @pytest.mark.asyncio
    async def test_comparar_con_sede_especifica(self, comparison_engine):
        """Test 5: Comparación filtrando por sede."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["aceite", "girasol"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.sede_id == "SEDE-001"
        assert resultado.comparables is True

    @pytest.mark.asyncio
    async def test_comparar_sin_sede(self, comparison_engine):
        """Test: Comparación sin especificar sede (usa default del proveedor)."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["aceite", "girasol"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD
        )

        resultado = await comparison_engine.comparar(solicitud, None)

        assert resultado.sede_id is None
        assert resultado.comparables is True


# ============================================================
# TESTS PRODUCTOS SIN STOCK
# ============================================================

class TestProductosSinStock:
    """Tests para manejo de productos sin stock."""

    @pytest.mark.asyncio
    async def test_comparar_con_producto_sin_stock(self, comparison_engine):
        """Test 6: Comparación incluyendo producto sin stock (huevos)."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["huevos", "aceite"],
            tipo_comparacion=TipoComparacion.COMPLETA,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        # Los huevos tienen stock=0, aceite tiene stock
        # Debería ser comparable (al menos 2 con stock)
        assert resultado.comparables is True

        # Verificar que huevos está marcado sin stock
        huevos_item = next((p for p in resultado.productos if "huevo" in p.producto.nombre.lower()), None)
        assert huevos_item is not None
        assert huevos_item.producto.disponible is False
        assert huevos_item.producto.stock == 0
        assert any("sin stock" in r.lower() for r in huevos_item.razones)

    @pytest.mark.asyncio
    async def test_comparar_todos_sin_stock(self, comparison_engine):
        """Test: Todos los productos sin stock."""
        # Modificar mock para que todo esté sin stock
        # Este test requeriría otro fixture, lo omitimos por ahora
        pass


# ============================================================
# TESTS PRESENTACIÓN AMBIGUA
# ============================================================

class TestPresentacionAmbigua:
    """Tests para detección de presentaciones ambiguas."""

    @pytest.mark.asyncio
    async def test_producto_sin_unidad_reconocible(self, comparison_engine, mock_proveedor):
        """Test 7: Producto sin unidad de medida clara."""
        # Agregar producto sin presentación clara
        producto_ambiguo = Producto(
            id="8",
            sku="AMBIGUO-001",
            nombre="Producto Misterioso",
            marca="MarcaX",
            presentacion="Presentación especial",
            categoria_id="otros",
            categoria_nombre="Otros",
            stock_por_sede={"SEDE-001": 10},
            fuente="fixture_desarrollo"
        )

        # Sobrescribir buscar para incluir este producto
        original_buscar = mock_proveedor.buscar

        async def buscar_con_ambiguo(query: str, filtros: Optional[FiltrosBusqueda] = None, tipo_busqueda: TipoBusqueda = TipoBusqueda.TEXTO) -> List[Producto]:
            resultados = await original_buscar(query, filtros, tipo_busqueda)
            if "misterioso" in query.lower() or "producto" in query.lower():
                resultados.append(producto_ambiguo)
            return resultados

        mock_proveedor.buscar = buscar_con_ambiguo
        mock_proveedor.obtener_precios_lote = AsyncMock(return_value={
            "8": PrecioInfo(producto_id="8", precio_final=10000)
        })
        mock_proveedor.verificar_stock_lote = AsyncMock(return_value={
            "8": StockInfo(producto_id="8", sede_id="SEDE-001", cantidad=10, disponible=True)
        })

        solicitud = SolicitudComparacion(
            terminos_busqueda=["producto misterioso", "aceite"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        # Debería detectar ambigüedad
        assert resultado.comparables is False
        assert any("ambigua" in lim.lower() or "no se puede calcular" in lim.lower() for lim in resultado.limitaciones)


# ============================================================
# TESTS TIPOS DE COMPARACIÓN
# ============================================================

class TestTiposComparacion:
    """Tests para cada tipo de comparación."""

    @pytest.mark.asyncio
    async def test_tipo_precio_total(self, comparison_engine):
        """Test 8: Comparación por precio total."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["arroz", "blanco"],
            tipo_comparacion=TipoComparacion.PRECIO_TOTAL,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.tipo_comparacion == TipoComparacion.PRECIO_TOTAL
        assert resultado.comparables is True

        # ARROZ-002 (2500) debería ganar sobre ARROZ-001 (4500)
        mejor = resultado.mejor_opcion
        assert mejor.sku == "ARROZ-002"

    @pytest.mark.asyncio
    async def test_tipo_cantidad(self, comparison_engine):
        """Test 9: Comparación por cantidad (más producto por peso)."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["arroz", "blanco"],
            tipo_comparacion=TipoComparacion.CANTIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.tipo_comparacion == TipoComparacion.CANTIDAD
        # ARROZ-001: 1000g / 4500 = 0.222 g/COP
        # ARROZ-002: 500g / 2500 = 0.200 g/COP
        # ARROZ-001 gana
        mejor = resultado.mejor_opcion
        assert mejor.sku == "ARROZ-001"

    @pytest.mark.asyncio
    async def test_tipo_disponibilidad(self, comparison_engine):
        """Test 10: Comparación por disponibilidad."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["huevos", "aceite"],
            tipo_comparacion=TipoComparacion.DISPONIBILIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.tipo_comparacion == TipoComparacion.DISPONIBILIDAD
        # Aceite tiene stock, huevos no
        mejor = resultado.mejor_opcion
        assert "aceite" in mejor.nombre.lower()
        assert mejor.disponible is True

    @pytest.mark.asyncio
    async def test_tipo_completa_con_contexto(self, comparison_engine):
        """Test 11: Comparación completa con contexto adicional."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["aceite", "girasol"],
            tipo_comparacion=TipoComparacion.COMPLETA,
            sede_id="SEDE-001",
            contexto_adicional="para freir"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.tipo_comparacion == TipoComparacion.COMPLETA
        assert resultado.comparables is True
        # El contexto "para freir" debería favorecer aceites vegetales sobre oliva
        assert "freir" in resultado.explicacion.lower() or "contexto" in resultado.explicacion.lower()


# ============================================================
# TESTS COMPARACIÓN POR SKU SELECCIONADOS
# ============================================================

class TestComparacionPorSKU:
    """Tests para comparar productos específicos por SKU."""

    @pytest.mark.asyncio
    async def test_comparar_skus_seleccionados(self, comparison_engine):
        """Test 12: Comparar lista específica de SKUs."""
        resultado = await comparison_engine.comparar_productos_seleccionados(
            sku_list=["ACEITE-001", "ACEITE-002"],
            tipo=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        assert resultado.comparables is True
        assert len(resultado.productos) == 2
        skus = {p.producto.sku for p in resultado.productos}
        assert skus == {"ACEITE-001", "ACEITE-002"}

    @pytest.mark.asyncio
    async def test_comparar_sku_inexistente(self, comparison_engine):
        """Test: SKU que no existe."""
        resultado = await comparison_engine.comparar_productos_seleccionados(
            sku_list=["ACEITE-001", "SKU-INEXISTENTE"],
            tipo=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        assert resultado.comparables is False
        # El mensaje real es "Se necesitan al menos 2 productos válidos para comparar."
        assert "al menos 2" in resultado.explicacion.lower() or "insuficientes" in resultado.explicacion.lower()


# ============================================================
# TESTS FORMATEO PARA AGENTE
# ============================================================

class TestFormateoAgente:
    """Tests para formateo de respuesta conversacional."""

    @pytest.mark.asyncio
    async def test_formatear_para_agente(self, comparison_engine):
        """Test 13: Formateo para respuesta del agente."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["arroz", "blanco"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")
        formateado = comparison_engine.formatear_para_agente(resultado)

        assert "Comparación detallada" in formateado
        assert "ARROZ" in formateado.upper()
        assert "$" in formateado
        assert "COP" in formateado

    @pytest.mark.asyncio
    async def test_formatear_vacio(self, comparison_engine):
        """Test: Formateo de respuesta vacía."""
        respuesta = ComparacionResponse(
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            criterio="Test",
            productos=[],
            explicacion="No hay productos",
            comparables=False
        )

        formateado = comparison_engine.formatear_para_agente(respuesta)
        assert formateado == "No hay productos"


# ============================================================
# TESTS UNIDADES ESPECIALES
# ============================================================

class TestUnidadesEspeciales:
    """Tests para docena, pack, litros."""

    @pytest.mark.asyncio
    async def test_comparar_huevos_docena(self, comparison_engine):
        """Test 14: Comparación huevos por docena."""
        # Solo huevos disponibles
        solicitud = SolicitudComparacion(
            terminos_busqueda=["huevos", "aa"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        # Huevos sin stock, pero debería detectar unidad docena
        # Como no hay 2+ productos con stock, no es comparable
        assert resultado.comparables is False
        assert "al menos 2" in resultado.explicacion.lower() or "stock" in resultado.explicacion.lower()

    @pytest.mark.asyncio
    async def test_comparar_leche_litros(self, comparison_engine):
        """Test: Comparación leche en litros."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["leche", "entera"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.comparables is False  # Solo 1 producto
        assert "al menos 2" in resultado.explicacion.lower()


# ============================================================
# TESTS EDGE CASES
# ============================================================

class TestEdgeCases:
    """Tests de casos borde."""

    @pytest.mark.asyncio
    async def test_precios_iguales(self, comparison_engine, mock_proveedor):
        """Test: Productos con mismo precio por unidad."""
        # Crear dos productos con mismo precio unitario
        p1 = Producto(
            id="9", sku="TEST-001", nombre="Test A", marca="M",
            presentacion="1kg", categoria_id="test", categoria_nombre="Test",
            unidad_medida="kg", contenido_neto=1,
            stock_por_sede={"SEDE-001": 10}, fuente="fixture_desarrollo"
        )
        p2 = Producto(
            id="10", sku="TEST-002", nombre="Test B", marca="M",
            presentacion="500g", categoria_id="test", categoria_nombre="Test",
            unidad_medida="g", contenido_neto=500,
            stock_por_sede={"SEDE-001": 10}, fuente="fixture_desarrollo"
        )

        # Agregar al buscar original
        original_buscar = mock_proveedor.buscar

        async def buscar_test(query: str, filtros: Optional[FiltrosBusqueda] = None, tipo_busqueda: TipoBusqueda = TipoBusqueda.TEXTO) -> List[Producto]:
            if "test" in query.lower():
                return [p1, p2]
            return await original_buscar(query, filtros, tipo_busqueda)

        mock_proveedor.buscar = buscar_test
        mock_proveedor.obtener_precios_lote = AsyncMock(return_value={
            "9": PrecioInfo(producto_id="9", precio_final=10000),
            "10": PrecioInfo(producto_id="10", precio_final=5000),
        })
        mock_proveedor.verificar_stock_lote = AsyncMock(return_value={
            "9": StockInfo(producto_id="9", sede_id="SEDE-001", cantidad=10, disponible=True),
            "10": StockInfo(producto_id="10", sede_id="SEDE-001", cantidad=10, disponible=True),
        })

        solicitud = SolicitudComparacion(
            terminos_busqueda=["test", "producto"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        # Ambos: 10 COP/g - deberían tener misma puntuación
        assert resultado.comparables is True
        puntuaciones = [p.puntuacion for p in resultado.productos]
        assert abs(puntuaciones[0] - puntuaciones[1]) < 1  # Casi iguales

    @pytest.mark.asyncio
    async def test_un_solo_producto(self, comparison_engine):
        """Test: Búsqueda que retorna un solo producto."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["leche", "entera"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.comparables is False
        assert "al menos 2" in resultado.explicacion.lower()

    @pytest.mark.asyncio
    async def test_sin_resultados_busqueda(self, comparison_engine):
        """Test: Búsqueda sin resultados."""
        solicitud = SolicitudComparacion(
            terminos_busqueda=["producto_inexistente_xyz", "otro_inexistente"],
            tipo_comparacion=TipoComparacion.PRECIO_POR_UNIDAD,
            sede_id="SEDE-001"
        )

        resultado = await comparison_engine.comparar(solicitud, "SEDE-001")

        assert resultado.comparables is False
        assert "0 productos" in resultado.explicacion or "encontraron" in resultado.explicacion


# ============================================================
# TESTS EXTRACCIÓN UNIDAD Y CONTENIDO
# ============================================================

class TestExtraccionUnidad:
    """Tests para extracción de unidad y contenido del nombre/presentación."""

    def test_extraer_ml(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Aceite 900ml", None)
        assert unidad == "ml"
        assert cantidad == 900

    def test_extraer_l(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Leche 1L", None)
        assert unidad == "l"
        assert cantidad == 1

    def test_extraer_kg(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Arroz 1kg", None)
        assert unidad == "kg"
        assert cantidad == 1

    def test_extraer_g(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Sal 500g", None)
        assert unidad == "g"
        assert cantidad == 500

    def test_extraer_x_unidades(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Huevos x 12", None)
        assert unidad == "und"
        assert cantidad == 12

    def test_extraer_docena(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Huevos 1 docena", None)
        assert unidad == "doc"
        assert cantidad == 1

    def test_extraer_pack(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Yogurt pack 6", None)
        assert unidad == "pack"
        assert cantidad == 6

    def test_extraer_desde_presentacion(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Aceite", "Botella 900ml")
        assert unidad == "ml"
        assert cantidad == 900

    def test_extraer_decimal(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Aceite 1.5L", None)
        assert unidad == "l"
        assert cantidad == 1.5

    def test_extraer_coma_decimal(self, comparison_engine):
        unidad, cantidad = comparison_engine._extraer_unidad_y_contenido("Aceite 1,5L", None)
        assert unidad == "l"
        assert cantidad == 1.5


# ============================================================
# TESTS PUNTUACIONES
# ============================================================

class TestPuntuaciones:
    """Tests para cálculo de puntuaciones."""

    def test_puntuar_precio_total(self, comparison_engine):
        # Crear productos analisis mock con estructura correcta
        from app.schemas.comparison import ProductoComparacion

        pc1 = ProductoComparacion(id="1", sku="TEST-1", nombre="Test 1", precio_final=10000, tiene_promocion=False)
        pc2 = ProductoComparacion(id="2", sku="TEST-2", nombre="Test 2", precio_final=20000, tiene_promocion=False)

        p1 = MagicMock()
        p1.producto_comparacion = pc1
        p1.advertencias = []

        p2 = MagicMock()
        p2.producto_comparacion = pc2
        p2.advertencias = []

        items = comparison_engine._puntuar_precio_total([p1, p2])
        assert len(items) == 2
        # p1 más barato -> mayor puntuación
        assert items[0].puntuacion > items[1].puntuacion

    def test_puntuar_disponibilidad(self, comparison_engine):
        from app.schemas.comparison import ProductoComparacion

        pc1 = ProductoComparacion(id="1", sku="TEST-1", nombre="Test 1", precio_final=10000, disponible=True, stock=10)
        pc2 = ProductoComparacion(id="2", sku="TEST-2", nombre="Test 2", precio_final=20000, disponible=False, stock=0)

        p1 = MagicMock()
        p1.producto_comparacion = pc1
        p1.advertencias = []

        p2 = MagicMock()
        p2.producto_comparacion = pc2
        p2.advertencias = []

        items = comparison_engine._puntuar_disponibilidad([p1, p2])
        assert items[0].puntuacion == 100
        assert items[1].puntuacion == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])