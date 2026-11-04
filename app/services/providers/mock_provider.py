"""
MockProvider - Proveedor de catálogo SOLO para desarrollo y pruebas.

⚠️  IMPORTANTE: Este proveedor NUNCA debe usarse en producción.
     Está estrictamente aislado para desarrollo y testing.
     Los datos son FIXTURES FICTICIOS y no representan información comercial real.

Cuando MasControl esté conectado, este proveedor se deshabilita automáticamente
mediante la configuración CATALOG_CONNECTED=false y el ProveedorRegistry.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.services.providers.base import (
    ProductProvider,
    Producto,
    FiltrosBusqueda,
    StockInfo,
    PrecioInfo,
    TipoBusqueda,
    ComparacionCriterio,
    ComparacionResultado,
    Promocion,
    ProveedorNoDisponibleError,
    ProductoNoEncontradoError,
)

# Importar fixtures desde módulo separado (tests/fixtures)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tests', 'fixtures'))

from tests.fixtures.mock_catalog import (
    obtener_productos_fixture,
    obtener_stock_fixture,
    obtener_promociones_fixture,
    MOCK_CATEGORIAS,
    MOCK_SEDES,
)


class MockProvider:
    """
    Proveedor MOCK para desarrollo y testing.

    ⚠️  ADVERTENCIA: Este proveedor usa DATOS FICTICIOS.
    NO debe usarse en producción bajo ninguna circunstancia.
    El ProveedorRegistry impide su uso cuando DEBUG=False.
    """

    nombre = "mock"
    version = "1.0.0-dev"
    _inicializado = False

    def __init__(self):
        if not MockProvider._inicializado:
            # Forzar inicialización de fixtures
            obtener_productos_fixture()
            obtener_stock_fixture()
            obtener_promociones_fixture()
            MockProvider._inicializado = True

    @property
    def esta_disponible(self) -> bool:
        # Siempre disponible en desarrollo (el registry controla cuándo usarlo)
        return True

    async def health_check(self) -> Dict[str, Any]:
        productos = obtener_productos_fixture()
        return {
            "proveedor": self.nombre,
            "version": self.version,
            "estado": "ok",
            "productos_cargados": len(productos),
            "advertencia": "PROVEEDOR MOCK - Solo desarrollo/testing. NO usar en producción.",
            "fuente_datos": "fixtures_locales",
            "categorias": len(MOCK_CATEGORIAS),
            "sedes": len(MOCK_SEDES),
        }

    # ==================== BÚSQUEDA Y LISTADO ====================

    async def buscar(
        self,
        query: str,
        filtros: Optional[FiltrosBusqueda] = None,
        tipo_busqueda: TipoBusqueda = TipoBusqueda.TEXTO
    ) -> List[Producto]:
        """Búsqueda textual simple sobre fixtures."""
        await asyncio.sleep(0.01)  # Simular latencia

        query_lower = query.lower().strip()
        if not query_lower:
            return []

        productos = obtener_productos_fixture()
        stock_data = obtener_stock_fixture()
        resultados = []

        for prod in productos.values():
            # Filtrar por sede si se especifica
            if filtros and filtros.sede_id:
                stock = stock_data.get(prod.id, {}).get(filtros.sede_id, 0)
                if filtros.solo_con_stock and stock <= 0:
                    continue

            # Filtrar por categoría
            if filtros and filtros.categoria_id and prod.categoria_id != filtros.categoria_id:
                continue

            # Filtrar por precio
            if filtros and filtros.precio_min is not None and prod.precio_final < filtros.precio_min:
                continue
            if filtros and filtros.precio_max is not None and prod.precio_final > filtros.precio_max:
                continue

            # Búsqueda textual en nombre, descripción, etiquetas, ingredientes
            texto_busqueda = " ".join([
                prod.nombre.lower(),
                prod.descripcion.lower() if prod.descripcion else "",
                prod.descripcion_corta.lower() if prod.descripcion_corta else "",
                " ".join(prod.etiquetas).lower(),
                " ".join(prod.ingredientes_receta).lower(),
                prod.marca.lower() if prod.marca else "",
            ])

            # Matching simple (en producción sería semántico/vectorial)
            if query_lower in texto_busqueda:
                # Clonar y actualizar stock dinámicamente
                p = Producto(**prod.__dict__)
                p.stock_total = sum(stock_data.get(prod.id, {}).values())
                p.stock_por_sede = stock_data.get(prod.id, {}).copy()
                resultados.append(p)

        # Ordenar
        if filtros:
            if filtros.ordenar_por == "precio_asc":
                resultados.sort(key=lambda x: x.precio_final)
            elif filtros.ordenar_por == "precio_desc":
                resultados.sort(key=lambda x: x.precio_final, reverse=True)

        # Limitar
        if filtros:
            inicio = filtros.offset
            fin = inicio + filtros.limite
            resultados = resultados[inicio:fin]

        return resultados

    async def obtener_por_id(self, producto_id: str) -> Optional[Producto]:
        productos = obtener_productos_fixture()
        stock_data = obtener_stock_fixture()
        prod = productos.get(producto_id)
        if not prod:
            return None
        p = Producto(**prod.__dict__)
        p.stock_total = sum(stock_data.get(prod.id, {}).values())
        p.stock_por_sede = stock_data.get(prod.id, {}).copy()
        return p

    async def obtener_por_sku(self, sku: str) -> Optional[Producto]:
        productos = obtener_productos_fixture()
        for prod in productos.values():
            if prod.sku == sku:
                return await self.obtener_por_id(prod.id)
        return None

    async def obtener_por_codigo_barras(self, ean13: str) -> Optional[Producto]:
        productos = obtener_productos_fixture()
        for prod in productos.values():
            if prod.codigo_barras == ean13:
                return await self.obtener_por_id(prod.id)
        return None

    async def listar_por_categoria(
        self,
        categoria_id: str,
        filtros: Optional[FiltrosBusqueda] = None
    ) -> List[Producto]:
        return await self.buscar("", filtros=FiltrosBusqueda(categoria_id=categoria_id, **(filtros.__dict__ if filtros else {})))

    async def listar_novedades(self, limite: int = 10, sede_id: Optional[str] = None) -> List[Producto]:
        productos = obtener_productos_fixture()
        stock_data = obtener_stock_fixture()
        # Simular novedades: últimos agregados
        productos_lista = list(productos.values())[-limite:]
        resultado = []
        for prod in productos_lista:
            p = Producto(**prod.__dict__)
            p.stock_total = sum(stock_data.get(prod.id, {}).values())
            p.stock_por_sede = stock_data.get(prod.id, {}).copy()
            resultado.append(p)
        return resultado

    async def listar_mas_vendidos(
        self,
        periodo_dias: int = 30,
        limite: int = 10,
        sede_id: Optional[str] = None
    ) -> List[Producto]:
        productos = obtener_productos_fixture()
        stock_data = obtener_stock_fixture()
        # Simular: productos con más stock (mock)
        productos_lista = list(productos.values())[:limite]
        resultado = []
        for prod in productos_lista:
            p = Producto(**prod.__dict__)
            p.stock_total = sum(stock_data.get(prod.id, {}).values())
            p.stock_por_sede = stock_data.get(prod.id, {}).copy()
            resultado.append(p)
        return resultado

    # ==================== PRECIOS Y STOCK ====================

    async def obtener_precio(
        self,
        producto_id: str,
        sede_id: Optional[str] = None,
        cliente_id: Optional[str] = None
    ) -> PrecioInfo:
        productos = obtener_productos_fixture()
        prod = productos.get(producto_id)
        if not prod:
            raise ProductoNoEncontradoError(self.nombre, producto_id)

        # Simular variación de precio por sede
        precio_final = prod.precio_final
        tiene_promo = prod.tiene_promocion
        promo_desc = None
        promo_id = None

        if sede_id:
            # Verificar promociones para esta sede
            for promo in obtener_promociones_fixture():
                if promo.activa and producto_id in promo.productos_ids:
                    if not promo.sede_ids or sede_id in promo.sede_ids:
                        if promo.tipo == "descuento_porcentaje":
                            precio_final = round(prod.precio_final * (1 - promo.valor / 100))
                            tiene_promo = True
                            promo_desc = promo.descripcion
                            promo_id = promo.id
                            break

        return PrecioInfo(
            producto_id=producto_id,
            sede_id=sede_id,
            precio_base=prod.precio_base,
            precio_final=precio_final,
            moneda="COP",
            tiene_promocion=tiene_promo,
            promocion_id=promo_id,
            promocion_descripcion=promo_desc,
            precio_por_unidad=prod.precio_por_unidad_base,
            unidad_medida=prod.unidad_medida,
        )

    async def obtener_precios_lote(
        self,
        producto_ids: List[str],
        sede_id: Optional[str] = None
    ) -> Dict[str, PrecioInfo]:
        resultados = {}
        for pid in producto_ids:
            try:
                resultados[pid] = await self.obtener_precio(pid, sede_id)
            except ProductoNoEncontradoError:
                pass
        return resultados

    async def verificar_stock(
        self,
        producto_id: str,
        sede_id: str
    ) -> StockInfo:
        productos = obtener_productos_fixture()
        stock_data = obtener_stock_fixture()

        if producto_id not in productos:
            raise ProductoNoEncontradoError(self.nombre, producto_id)

        stock = stock_data.get(producto_id, {}).get(sede_id, 0)
        return StockInfo(
            producto_id=producto_id,
            sede_id=sede_id,
            cantidad=stock,
            disponible=stock > 0,
            reservado=0,
            en_camino=0,  # Mock: sin stock en camino
            actualizado_en=datetime.now(),
        )

    async def verificar_stock_lote(
        self,
        items: List[tuple[str, str]]
    ) -> Dict[str, StockInfo]:
        resultados = {}
        for prod_id, sede_id in items:
            try:
                resultados[f"{prod_id}:{sede_id}"] = await self.verificar_stock(prod_id, sede_id)
            except ProductoNoEncontradoError:
                pass
        return resultados

    # ==================== COMPARATIVAS ====================

    async def comparar_productos(self, criterio: ComparacionCriterio) -> ComparacionResultado:
        productos = []
        for pid in criterio.producto_ids:
            prod = await self.obtener_por_id(pid)
            if prod:
                if criterio.sede_id:
                    precio_info = await self.obtener_precio(pid, criterio.sede_id)
                    prod.precio_final = precio_info.precio_final
                    prod.tiene_promocion = precio_info.tiene_promocion
                productos.append(prod)

        if not productos:
            return ComparacionResultado(productos=[], resumen="No se encontraron productos para comparar")

        mejor_precio = min(productos, key=lambda p: p.precio_final)
        mejor_precio_unidad = min(
            [p for p in productos if p.precio_por_unidad_base],
            key=lambda p: p.precio_por_unidad_base,
            default=None
        )
        mejor_stock = max(productos, key=lambda p: p.stock_total)

        resumen = f"Comparación de {len(productos)} productos. "
        resumen += f"Mejor precio: {mejor_precio.nombre} (${mejor_precio.precio_final:,.0f}). "
        if mejor_precio_unidad:
            resumen += f"Mejor precio/unidad: {mejor_precio_unidad.nombre} (${mejor_precio_unidad.precio_por_unidad_base:,.0f}/{mejor_precio_unidad.unidad_medida}). "
        resumen += f"Mejor disponibilidad: {mejor_stock.nombre} ({mejor_stock.stock_total} und)."

        return ComparacionResultado(
            productos=productos,
            mejor_precio=mejor_precio,
            mejor_precio_por_unidad=mejor_precio_unidad,
            mejor_disponibilidad=mejor_stock,
            resumen=resumen,
        )

    async def obtener_alternativas(
        self,
        producto_id: str,
        limite: int = 5,
        sede_id: Optional[str] = None
    ) -> List[Producto]:
        productos = obtener_productos_fixture()
        stock_data = obtener_stock_fixture()
        prod = productos.get(producto_id)
        if not prod:
            return []

        # Buscar en misma categoría
        alternativas = [
            p for p in productos.values()
            if p.categoria_id == prod.categoria_id and p.id != producto_id
        ][:limite]

        resultado = []
        for p in alternativas:
            prod_copy = Producto(**p.__dict__)
            prod_copy.stock_total = sum(stock_data.get(p.id, {}).values())
            prod_copy.stock_por_sede = stock_data.get(p.id, {}).copy()
            resultado.append(prod_copy)

        return resultado

    async def obtener_complementos(
        self,
        producto_id: str,
        limite: int = 5
    ) -> List[Producto]:
        productos = obtener_productos_fixture()
        stock_data = obtener_stock_fixture()
        prod = productos.get(producto_id)
        if not prod:
            return []

        # Mapeo simple de complementos por categoría
        complementos_map = {
            "cat_001": ["cat_004", "cat_003"],  # Frutas -> Despensa, Lácteos
            "cat_002": ["cat_001", "cat_004"],  # Carnes -> Verduras, Despensa
            "cat_003": ["cat_010", "cat_004"],  # Lácteos -> Panadería, Despensa
            "cat_004": ["cat_001", "cat_002"],  # Despensa -> Verduras, Carnes
        }

        cats = complementos_map.get(prod.categoria_id, [])
        complementos = [
            p for p in productos.values()
            if p.categoria_id in cats
        ][:limite]

        resultado = []
        for p in complementos:
            prod_copy = Producto(**p.__dict__)
            prod_copy.stock_total = sum(stock_data.get(p.id, {}).values())
            prod_copy.stock_por_sede = stock_data.get(p.id, {}).copy()
            resultado.append(prod_copy)

        return resultado

    # ==================== PROMOCIONES ====================

    async def obtener_promociones_activas(
        self,
        sede_id: Optional[str] = None,
        categoria_id: Optional[str] = None
    ) -> List[Promocion]:
        ahora = datetime.now()
        activas = [
            p for p in obtener_promociones_fixture()
            if p.activa and p.fecha_inicio <= ahora <= p.fecha_fin
        ]

        if sede_id:
            activas = [p for p in activas if not p.sede_ids or sede_id in p.sede_ids]

        if categoria_id:
            activas = [p for p in activas if not p.categorias_ids or categoria_id in p.categorias_ids]

        return activas

    async def obtener_promociones_producto(
        self,
        producto_id: str,
        sede_id: Optional[str] = None
    ) -> List[Promocion]:
        ahora = datetime.now()
        return [
            p for p in obtener_promociones_fixture()
            if p.activa and producto_id in p.productos_ids
            and p.fecha_inicio <= ahora <= p.fecha_fin
            and (not p.sede_ids or not sede_id or sede_id in p.sede_ids)
        ]

    # ==================== RECETAS ====================

    async def buscar_ingredientes_receta(
        self,
        ingredientes: List[str],
        sede_id: Optional[str] = None,
        presupuesto_max: Optional[float] = None
    ) -> Dict[str, List[Producto]]:
        """Para cada ingrediente, busca los mejores productos."""
        resultado = {}
        for ing in ingredientes:
            productos = await self.buscar(ing, filtros=FiltrosBusqueda(
                sede_id=sede_id,
                solo_con_stock=True,
                limite=3,
                ordenar_por="precio_asc"
            ))
            if presupuesto_max:
                productos = [p for p in productos if p.precio_final <= presupuesto_max]
            resultado[ing] = productos
        return resultado

    async def calcular_costo_receta(
        self,
        ingredientes: List[Dict[str, Any]],
        sede_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calcula costo total de una receta."""
        total = 0.0
        por_ingrediente = {}
        productos_seleccionados = {}

        for ing in ingredientes:
            nombre = ing.get("ingrediente", "")
            cantidad = ing.get("cantidad", 1)
            unidad = ing.get("unidad", "unidad")

            productos = await self.buscar(nombre, filtros=FiltrosBusqueda(
                sede_id=sede_id,
                solo_con_stock=True,
                limite=1,
                ordenar_por="precio_asc"
            ))

            if productos:
                prod = productos[0]
                precio_unitario = prod.precio_final
                # Ajustar por cantidad/unidad si es posible
                costo = precio_unitario * cantidad
                total += costo
                por_ingrediente[nombre] = {
                    "producto": prod.nombre,
                    "precio_unitario": precio_unitario,
                    "cantidad": cantidad,
                    "unidad": unidad,
                    "costo": costo,
                }
                productos_seleccionados[nombre] = prod.id
            else:
                por_ingrediente[nombre] = {
                    "producto": None,
                    "error": "No se encontró producto para este ingrediente",
                }

        return {
            "total": round(total, 2),
            "por_ingrediente": por_ingrediente,
            "productos_seleccionados": productos_seleccionados,
            "ahorro_vs_promedio": 0.0,  # Mock
        }

    # ==================== SINCRONIZACIÓN (NO APLICA A MOCK) ====================

    async def sincronizar_catalogo_completo(self) -> Dict[str, Any]:
        productos = obtener_productos_fixture()
        return {
            "proveedor": self.nombre,
            "estado": "no_aplica",
            "mensaje": "MockProvider no soporta sincronización - usa fixtures locales",
            "productos": len(productos),
        }

    async def sincronizar_incremental(self, desde: datetime) -> Dict[str, Any]:
        return {
            "proveedor": self.nombre,
            "estado": "no_aplica",
            "mensaje": "MockProvider no soporta sincronización incremental",
        }

    async def obtener_ultima_sincronizacion(self) -> Optional[datetime]:
        return None


# Instancia singleton para uso en desarrollo (controlada por ProveedorRegistry)
mock_provider = MockProvider()