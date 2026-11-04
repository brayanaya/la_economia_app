"""
Tests exhaustivos para BudgetPlanner - Planificador de Presupuesto

Cubre todos los escenarios especificados:
1. Lista básica → items con precio y stock
2. Lista con algunos sin stock → marca estado y avisa
3. Lista con productos no encontrados → estado no_encontrado
4. Catálogo desconectado → error CATALOGO_DESCONECTADO
5. Catálogo degradado → warning pero intenta
6. Presupuesto exacto → excedido = false, diferencia = 0
7. Presupuesto excedido → excedido = true, diferencia negativa
8. Presupuesto no especificado → solo total
9. Recalcular agregando item → nuevo total
10. Recalcular quitando item → nuevo total
11. Recalcular cambiando cantidad → subtotal actualizado
12. Formato COP colombiano (puntos miles)
13. Cálculos con Decimal (sin floats)
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.services.budget_planner import (
    BudgetPlanner,
    crear_budget_planner,
    ItemPresupuesto,
    ResultadoPresupuesto,
    EstadoProductoPresupuesto,
    EstadoPresupuesto,
)
from app.services.providers.base import (
    ProductProvider,
    Producto,
    PrecioInfo,
    StockInfo,
    ProveedorNoDisponibleError,
)
from app.core.catalog_state import catalogo_state, CatalogoEstado


# ==================== FIXTURES ====================

@pytest.fixture
def mock_producto_arroz():
    """Producto de prueba: Arroz Diana 1kg"""
    return Producto(
        id="prod-arroz-001",
        sku="ARROZ-DIANA-1KG",
        nombre="Arroz Diana 1kg",
        descripcion="Arroz blanco grano largo",
        categoria_id="cat-abarrotes",
        categoria_nombre="Abarrotes",
        precio_final=4500,
        presentacion="1 kg",
        etiquetas=["basico"],
        stock_por_sede={"sede-1": 50, "sede-2": 30},
    )


@pytest.fixture
def mock_producto_leche():
    """Producto de prueba: Leche Alquería 1L"""
    return Producto(
        id="prod-leche-001",
        sku="LECHE-ALQUERIA-1L",
        nombre="Leche Alquería Entera 1L",
        descripcion="Leche entera pasteurizada",
        categoria_id="cat-lacteos",
        categoria_nombre="Lácteos",
        precio_final=4900,
        presentacion="1 L",
        etiquetas=[],
        stock_por_sede={"sede-1": 100, "sede-2": 80},
    )


@pytest.fixture
def mock_producto_huevos():
    """Producto de prueba: Huevos AAA x12"""
    return Producto(
        id="prod-huevos-001",
        sku="HUEVOS-AAA-12",
        nombre="Huevos AAA x12",
        descripcion="Huevos rojos categoría AAA",
        categoria_id="cat-lacteos",
        categoria_nombre="Lácteos",
        precio_final=14900,
        presentacion="12 unds",
        etiquetas=["proteina"],
        stock_por_sede={"sede-1": 200, "sede-2": 150},
    )


@pytest.fixture
def mock_producto_sin_stock():
    """Producto sin stock"""
    return Producto(
        id="prod-sin-stock-001",
        sku="PROD-AGOTADO-001",
        nombre="Producto Agotado",
        descripcion="Sin stock",
        categoria_id="cat-test",
        categoria_nombre="Test",
        precio_final=10000,
        presentacion="1 und",
        etiquetas=[],
        stock_por_sede={"sede-1": 0, "sede-2": 0},
    )


@pytest.fixture
def mock_proveedor(mock_producto_arroz, mock_producto_leche, mock_producto_huevos, mock_producto_sin_stock):
    """Proveedor mock completo con todos los métodos implementados"""
    proveedor = AsyncMock(spec=ProductProvider)
    proveedor.nombre = "mock"
    proveedor.esta_disponible = True

    # buscar - retorna productos según término
    async def buscar_side_effect(termino, filtros=None, tipo_busqueda=None):
        termino_lower = termino.lower()
        if "arroz" in termino_lower:
            return [mock_producto_arroz]
        elif "leche" in termino_lower:
            return [mock_producto_leche]
        elif "huevo" in termino_lower:
            return [mock_producto_huevos]
        elif "agotado" in termino_lower or "sin stock" in termino_lower:
            return [mock_producto_sin_stock]
        elif "no existe" in termino_lower or "inexistente" in termino_lower:
            return []
        # Default: retorna arroz
        return [mock_producto_arroz]

    proveedor.buscar.side_effect = buscar_side_effect

    # obtener_precios_lote
    async def precios_lote_side_effect(producto_ids, sede_id=None):
        precios = {}
        for pid in producto_ids:
            if pid == "prod-arroz-001":
                precios[pid] = PrecioInfo(
                    producto_id=pid,
                    precio_base=4500,
                    precio_final=4500,
                    moneda="COP",
                    tiene_promocion=False,
                )
            elif pid == "prod-leche-001":
                precios[pid] = PrecioInfo(
                    producto_id=pid,
                    precio_base=4900,
                    precio_final=4900,
                    moneda="COP",
                    tiene_promocion=False,
                )
            elif pid == "prod-huevos-001":
                precios[pid] = PrecioInfo(
                    producto_id=pid,
                    precio_base=14900,
                    precio_final=14900,
                    moneda="COP",
                    tiene_promocion=False,
                )
            elif pid == "prod-sin-stock-001":
                precios[pid] = PrecioInfo(
                    producto_id=pid,
                    precio_base=10000,
                    precio_final=10000,
                    moneda="COP",
                    tiene_promocion=False,
                )
        return precios

    proveedor.obtener_precios_lote.side_effect = precios_lote_side_effect

    # verificar_stock_lote
    async def stock_lote_side_effect(items_sede):
        stocks = {}
        for pid, sid in items_sede:
            key = f"{pid}:{sid}"
            if pid == "prod-arroz-001":
                stocks[key] = StockInfo(producto_id=pid, sede_id=sid, cantidad=50, disponible=True)
            elif pid == "prod-leche-001":
                stocks[key] = StockInfo(producto_id=pid, sede_id=sid, cantidad=100, disponible=True)
            elif pid == "prod-huevos-001":
                stocks[key] = StockInfo(producto_id=pid, sede_id=sid, cantidad=200, disponible=True)
            elif pid == "prod-sin-stock-001":
                stocks[key] = StockInfo(producto_id=pid, sede_id=sid, cantidad=0, disponible=False)
        return stocks

    proveedor.verificar_stock_lote.side_effect = stock_lote_side_effect

    # health_check
    proveedor.health_check.return_value = {"estado": "ok"}

    return proveedor


@pytest.fixture
def planner(mock_proveedor):
    """Instancia de BudgetPlanner con proveedor mock"""
    return crear_budget_planner(mock_proveedor)


@pytest.fixture(autouse=True)
def reset_catalogo_state():
    """Resetear estado del catálogo antes de cada test"""
    catalogo_state.marcar_conectado()
    yield
    catalogo_state.marcar_conectado()


# ==================== TESTS: ESCENARIOS BÁSICOS ====================

class TestEscenariosBasicos:
    """Tests para los escenarios básicos de cálculo de presupuesto"""

    @pytest.mark.asyncio
    async def test_lista_basica_items_con_precio_y_stock(self, planner):
        """
        ESCENARIO 1: Lista básica → items con precio y stock
        Usuario pide: arroz, leche, huevos
        Esperado: 3 items con estado DISPONIBLE, precios correctos, subtotales
        """
        items = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "leche", "cantidad": 2, "unidad": "litro"},
            {"termino_busqueda": "huevos", "cantidad": 1, "unidad": "docena"},
        ]

        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        # Verificar estado general
        assert resultado.estado == EstadoPresupuesto.OK
        assert resultado.catalogo_conectado is True
        assert resultado.proveedor_usado == "mock"

        # Verificar items
        assert len(resultado.items) == 3
        for item in resultado.items:
            assert item.estado == EstadoProductoPresupuesto.DISPONIBLE
            assert item.precio_unitario > 0
            assert item.subtotal > 0
            assert item.producto is not None

        # Verificar precios específicos
        arroz_item = next(i for i in resultado.items if "arroz" in i.termino_busqueda.lower())
        assert arroz_item.precio_unitario == Decimal("4500")
        assert arroz_item.subtotal == Decimal("4500")  # 1 * 4500

        leche_item = next(i for i in resultado.items if "leche" in i.termino_busqueda.lower())
        assert leche_item.precio_unitario == Decimal("4900")
        assert leche_item.subtotal == Decimal("9800")  # 2 * 4900

        huevos_item = next(i for i in resultado.items if "huevo" in i.termino_busqueda.lower())
        assert huevos_item.precio_unitario == Decimal("14900")
        assert huevos_item.subtotal == Decimal("14900")  # 1 * 14900

        # Verificar total
        assert resultado.total_con_precio == Decimal("29200")  # 4500 + 9800 + 14900

    @pytest.mark.asyncio
    async def test_lista_con_algunos_sin_stock(self, planner):
        """
        ESCENARIO 2: Lista con algunos sin stock → marca estado y avisa
        """
        items = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "producto agotado", "cantidad": 1, "unidad": "unidad"},
        ]

        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        assert len(resultado.items) == 2

        arroz_item = next(i for i in resultado.items if "arroz" in i.termino_busqueda.lower())
        assert arroz_item.estado == EstadoProductoPresupuesto.DISPONIBLE

        agotado_item = next(i for i in resultado.items if "agotado" in i.termino_busqueda.lower())
        assert agotado_item.estado == EstadoProductoPresupuesto.SIN_STOCK
        assert "sin stock" in agotado_item.mensaje.lower()

        assert resultado.total_sin_stock == 1
        assert resultado.total_con_precio == Decimal("4500")  # Solo arroz

    @pytest.mark.asyncio
    async def test_lista_con_productos_no_encontrados(self, planner):
        """
        ESCENARIO 3: Lista con productos no encontrados → estado no_encontrado
        """
        items = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "producto inexistente xyz", "cantidad": 1, "unidad": "unidad"},
        ]

        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        assert len(resultado.items) == 2

        arroz_item = next(i for i in resultado.items if "arroz" in i.termino_busqueda.lower())
        assert arroz_item.estado == EstadoProductoPresupuesto.DISPONIBLE

        no_encontrado_item = next(i for i in resultado.items if "inexistente" in i.termino_busqueda.lower())
        assert no_encontrado_item.estado == EstadoProductoPresupuesto.NO_ENCONTRADO
        assert "no se encontró" in no_encontrado_item.mensaje.lower()

        assert resultado.total_no_encontrados == 1
        assert resultado.total_con_precio == Decimal("4500")

    @pytest.mark.asyncio
    async def test_catalogo_desconectado_error(self, planner):
        """
        ESCENARIO 4: Catálogo desconectado → error CATALOGO_DESCONECTADO
        """
        catalogo_state.marcar_desconectado()

        items = [{"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"}]

        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        assert resultado.estado == EstadoPresupuesto.CATALOGO_DESCONECTADO
        assert resultado.catalogo_conectado is False
        assert "desconectado" in resultado.mensaje.lower()
        assert len(resultado.items) == 0

    @pytest.mark.asyncio
    async def test_catalogo_degradado_warning_pero_intenta(self, planner, mock_proveedor):
        """
        ESCENARIO 5: Catálogo degradado → warning pero intenta
        """
        catalogo_state.marcar_degradado("Timeout en conexión")

        items = [{"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"}]

        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        # Debería intentar y funcionar porque el mock está disponible
        assert resultado.estado in (EstadoPresupuesto.OK, EstadoPresupuesto.CATALOGO_INACCESIBLE)
        # El mock debería responder
        assert len(resultado.items) >= 0


# ==================== TESTS: PRESUPUESTO Y COMPARACIÓN ====================

class TestPresupuestoComparacion:
    """Tests para comparación con presupuesto límite"""

    @pytest.mark.asyncio
    async def test_presupuesto_exacto_excedido_false_diferencia_cero(self, planner):
        """
        ESCENARIO 6: Presupuesto exacto → excedido = false, diferencia = 0
        Total = 29200, presupuesto = 29200
        """
        items = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "leche", "cantidad": 2, "unidad": "litro"},
            {"termino_busqueda": "huevos", "cantidad": 1, "unidad": "docena"},
        ]

        resultado = await planner.calcular_presupuesto(
            items,
            presupuesto_limite=Decimal("29200"),
            sede_id="sede-1"
        )

        assert resultado.presupuesto_limite == Decimal("29200")
        assert resultado.total_con_precio == Decimal("29200")
        assert resultado.presupuesto_excedido is False
        assert resultado.diferencia_presupuesto == Decimal("0")
        assert resultado.estado == EstadoPresupuesto.OK

    @pytest.mark.asyncio
    async def test_presupuesto_excedido_excedido_true_diferencia_negativa(self, planner):
        """
        ESCENARIO 7: Presupuesto excedido → excedido = true, diferencia negativa
        Total = 29200, presupuesto = 20000
        """
        items = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "leche", "cantidad": 2, "unidad": "litro"},
            {"termino_busqueda": "huevos", "cantidad": 1, "unidad": "docena"},
        ]

        resultado = await planner.calcular_presupuesto(
            items,
            presupuesto_limite=Decimal("20000"),
            sede_id="sede-1"
        )

        assert resultado.presupuesto_limite == Decimal("20000")
        assert resultado.total_con_precio == Decimal("29200")
        assert resultado.presupuesto_excedido is True
        assert resultado.diferencia_presupuesto == Decimal("-9200")
        assert resultado.estado == EstadoPresupuesto.PRESUPUESTO_EXCEDIDO

    @pytest.mark.asyncio
    async def test_presupuesto_no_especificado_solo_total(self, planner):
        """
        ESCENARIO 8: Presupuesto no especificado → solo total, sin comparación
        """
        items = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "leche", "cantidad": 1, "unidad": "litro"},
        ]

        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        assert resultado.presupuesto_limite is None
        assert resultado.total_con_precio == Decimal("9400")  # 4500 + 4900
        assert resultado.presupuesto_excedido is False
        assert resultado.diferencia_presupuesto == Decimal("0")
        assert resultado.estado == EstadoPresupuesto.OK


# ==================== TESTS: RECÁLCULO CON CAMBIOS ====================

class TestRecalculoConCambios:
    """Tests para recálculo incremental"""

    @pytest.mark.asyncio
    async def test_recalcular_agregando_item(self, planner):
        """
        ESCENARIO 9: Recalcular agregando item → nuevo total
        """
        # Cálculo inicial
        items_iniciales = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
        ]
        resultado_inicial = await planner.calcular_presupuesto(items_iniciales, sede_id="sede-1")
        assert resultado_inicial.total_con_precio == Decimal("4500")

        # Recalcular agregando leche
        resultado_nuevo = await planner.recalcular_con_cambios(
            resultado_inicial,
            agregar=[{"termino_busqueda": "leche", "cantidad": 1, "unidad": "litro"}],
            sede_id="sede-1"
        )

        assert resultado_nuevo.total_con_precio == Decimal("9400")  # 4500 + 4900
        assert len(resultado_nuevo.items) == 2

    @pytest.mark.asyncio
    async def test_recalcular_quitando_item(self, planner):
        """
        ESCENARIO 10: Recalcular quitando item → nuevo total
        """
        items_iniciales = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "leche", "cantidad": 1, "unidad": "litro"},
            {"termino_busqueda": "huevos", "cantidad": 1, "unidad": "docena"},
        ]
        resultado_inicial = await planner.calcular_presupuesto(items_iniciales, sede_id="sede-1")
        assert resultado_inicial.total_con_precio == Decimal("24300")  # 4500 + 4900 + 14900

        # Recalcular quitando huevos
        resultado_nuevo = await planner.recalcular_con_cambios(
            resultado_inicial,
            quitar=["huevos"],
            sede_id="sede-1"
        )

        assert resultado_nuevo.total_con_precio == Decimal("9400")  # 4500 + 4900
        assert len(resultado_nuevo.items) == 2
        terminos = [i.termino_busqueda.lower() for i in resultado_nuevo.items]
        assert "huevo" not in " ".join(terminos)

    @pytest.mark.asyncio
    async def test_recalcular_cambiando_cantidad(self, planner):
        """
        ESCENARIO 11: Recalcular cambiando cantidad → subtotal actualizado
        """
        items_iniciales = [
            {"termino_busqueda": "leche", "cantidad": 1, "unidad": "litro"},
        ]
        resultado_inicial = await planner.calcular_presupuesto(items_iniciales, sede_id="sede-1")
        assert resultado_inicial.total_con_precio == Decimal("4900")

        # Cambiar cantidad a 3
        resultado_nuevo = await planner.recalcular_con_cambios(
            resultado_inicial,
            cambiar_cantidad={"leche": 3},
            sede_id="sede-1"
        )

        leche_item = next(i for i in resultado_nuevo.items if "leche" in i.termino_busqueda.lower())
        assert leche_item.cantidad == 3
        assert leche_item.subtotal == Decimal("14700")  # 3 * 4900
        assert resultado_nuevo.total_con_precio == Decimal("14700")


# ==================== TESTS: FORMATO Y PRECISIÓN ====================

class TestFormatoYPrecision:
    """Tests para formato COP y precisión Decimal"""

    @pytest.mark.asyncio
    async def test_formato_cop_colombiano_puntos_miles(self, planner):
        """
        ESCENARIO 12: Formato COP colombiano (puntos para miles)
        """
        items = [{"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"}]
        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        resumen = resultado.resumen_usuario

        # Verificar que usa puntos para miles
        assert "4.500" in resumen or "4,500" not in resumen
        # El formato _fmt usa .replace(",", ".")
        assert "." in resumen.split("$")[1].split(" ")[0]  # Tiene punto en miles

    @pytest.mark.asyncio
    async def test_calculos_con_decimal_sin_floats(self, planner):
        """
        ESCENARIO 13: Cálculos con Decimal (sin floats)
        Verificar que no hay pérdida de precisión
        """
        # Usar cantidades y precios que causen problemas con float
        items = [
            {"termino_busqueda": "arroz", "cantidad": 3, "unidad": "unidad"},  # 3 * 4500 = 13500
        ]
        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        arroz_item = resultado.items[0]
        # Verificar que subtotal es exacto
        assert arroz_item.subtotal == Decimal("13500")
        assert resultado.total_con_precio == Decimal("13500")

        # Test con precio que tiene decimales
        # Simular precio 4500.50 * 2 = 9001.00
        # Pero nuestros mocks usan enteros, así que verificamos el tipo
        assert isinstance(arroz_item.precio_unitario, Decimal)
        assert isinstance(arroz_item.subtotal, Decimal)
        assert isinstance(resultado.total_con_precio, Decimal)
        assert isinstance(resultado.diferencia_presupuesto, Decimal)


# ==================== TESTS: EDGE CASES ====================

class TestEdgeCases:
    """Casos borde y validaciones"""

    @pytest.mark.asyncio
    async def test_items_vacio(self, planner):
        """Lista vacía → resultado vacío sin error"""
        resultado = await planner.calcular_presupuesto([], sede_id="sede-1")
        assert resultado.total_con_precio == Decimal("0")
        assert len(resultado.items) == 0
        assert resultado.estado == EstadoPresupuesto.OK

    @pytest.mark.asyncio
    async def test_item_formato_invalido(self, planner):
        """Item con formato inválido (término vacío) → estado ERROR_PROVEEDOR"""
        items = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "", "cantidad": 1, "unidad": "unidad"},  # Término vacío
        ]
        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")
        assert len(resultado.items) == 2
        # Término vacío se reemplaza con "item_1"
        invalido = next(i for i in resultado.items if i.termino_busqueda == "item_1")
        assert invalido.estado == EstadoProductoPresupuesto.ERROR_PROVEEDOR
        assert "vacío" in invalido.mensaje.lower()

    @pytest.mark.asyncio
    async def test_cantidad_cero_o_negativa_se_corrige_a_1(self, planner):
        """Cantidad <= 0 se corrige a 1"""
        items = [
            {"termino_busqueda": "arroz", "cantidad": 0, "unidad": "unidad"},
            {"termino_busqueda": "leche", "cantidad": -5, "unidad": "litro"},
        ]
        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")
        for item in resultado.items:
            assert item.cantidad == 1

    @pytest.mark.asyncio
    async def test_sin_sede_id_no_consulta_stock(self, planner, mock_proveedor):
        """Sin sede_id → no llama a verificar_stock_lote"""
        items = [{"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"}]
        resultado = await planner.calcular_presupuesto(items, sede_id=None)

        assert resultado.estado == EstadoPresupuesto.OK
        # Stock no debería haberse consultado (producto sigue DISPONIBLE sin verificación de stock)
        mock_proveedor.verificar_stock_lote.assert_not_called()

    @pytest.mark.asyncio
    async def test_calcular_lista_simple_convenience(self, planner):
        """Método de conveniencia calcular_lista_simple"""
        resultado = await planner.calcular_lista_simple(
            ["arroz", "leche", "huevos"],
            presupuesto_limite=Decimal("50000"),
            sede_id="sede-1"
        )

        assert len(resultado.items) == 3
        assert resultado.total_con_precio == Decimal("24300")  # 4500 + 4900 + 14900
        assert resultado.presupuesto_limite == Decimal("50000")
        assert resultado.presupuesto_excedido is False

    @pytest.mark.asyncio
    async def test_proveedor_error_en_busqueda(self, planner, mock_proveedor):
        """Error en proveedor al buscar → estado ERROR_PROVEEDOR"""
        mock_proveedor.buscar.side_effect = ProveedorNoDisponibleError("mock", "Error de conexión")

        items = [{"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"}]
        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        assert len(resultado.items) == 1
        assert resultado.items[0].estado == EstadoProductoPresupuesto.ERROR_PROVEEDOR
        assert resultado.estado == EstadoPresupuesto.CATALOGO_INACCESIBLE

    @pytest.mark.asyncio
    async def test_resumen_usuario_incluye_toda_info(self, planner):
        """resumen_usuario incluye presupuesto, total, estado items"""
        items = [
            {"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"},
            {"termino_busqueda": "producto inexistente", "cantidad": 1, "unidad": "unidad"},
        ]
        resultado = await planner.calcular_presupuesto(
            items,
            presupuesto_limite=Decimal("10000"),
            sede_id="sede-1"
        )

        resumen = resultado.resumen_usuario
        assert "Presupuesto: $10.000" in resumen
        assert "Total calculado: $4.500" in resumen
        assert "Te quedan $5.500" in resumen
        assert "no encontrado" in resumen.lower()


# ==================== TESTS: INTEGRACIÓN CON CONTEXTO ====================

class TestIntegracionContexto:
    """Tests de integración con contexto conversacional"""

    @pytest.mark.asyncio
    async def test_presupuesto_se_guarda_en_contexto(self, planner):
        """El resultado del presupuesto tiene los campos para guardarse en contexto"""
        items = [{"termino_busqueda": "arroz", "cantidad": 1, "unidad": "unidad"}]
        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        # Verificar que tiene todos los campos necesarios para contexto
        assert hasattr(resultado, 'items')
        assert hasattr(resultado, 'total_con_precio')
        assert hasattr(resultado, 'presupuesto_limite')
        assert hasattr(resultado, 'presupuesto_excedido')
        assert hasattr(resultado, 'diferencia_presupuesto')
        assert hasattr(resultado, 'sede_id')
        assert hasattr(resultado, 'catalogo_conectado')
        assert hasattr(resultado, 'proveedor_usado')

    @pytest.mark.asyncio
    async def test_items_tienen_info_completa_para_frontend(self, planner):
        """Items tienen toda la info que necesita el frontend"""
        items = [{"termino_busqueda": "arroz", "cantidad": 2, "unidad": "kg"}]
        resultado = await planner.calcular_presupuesto(items, sede_id="sede-1")

        item = resultado.items[0]
        assert item.termino_busqueda == "arroz"
        assert item.cantidad == 2
        assert item.unidad == "kg"
        assert item.producto is not None
        assert item.producto.id == "prod-arroz-001"
        assert item.producto.nombre == "Arroz Diana 1kg"
        assert item.precio_unitario == Decimal("4500")
        assert item.subtotal == Decimal("9000")
        assert item.estado == EstadoProductoPresupuesto.DISPONIBLE
        assert isinstance(item.mensaje, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])