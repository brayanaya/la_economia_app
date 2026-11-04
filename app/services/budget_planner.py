"""
Budget Planner - Planificador de Presupuesto para La Economía Aya

Servicio independiente de cálculos comerciales.
NO mezcla lógica de negocio con el LLM.
Utiliza el proveedor de catálogo autoritativo para precios y stock.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
import json

from app.services.providers.base import (
    ProductProvider,
    Producto,
    PrecioInfo,
    StockInfo,
    ProveedorNoDisponibleError,
    ProductoNoEncontradoError,
)
from app.core.catalog_state import catalogo_state, CatalogoEstado

logger = logging.getLogger(__name__)


class EstadoProductoPresupuesto(str, Enum):
    """Estados posibles de un producto en el presupuesto."""
    DISPONIBLE = "disponible"           # Encontrado, con precio y stock > 0
    SIN_STOCK = "sin_stock"             # Encontrado, con precio, pero stock = 0
    SIN_PRECIO = "sin_precio"           # Encontrado, pero sin precio verificable
    NO_ENCONTRADO = "no_encontrado"     # No existe en catálogo
    ERROR_PROVEEDOR = "error_proveedor" # Error consultando el proveedor
    AMBIGUO = "ambiguo"                 # Múltiples productos coinciden, requiere clarificación


class AmbiguedadProducto(Exception):
    """Excepción cuando hay múltiples productos que coinciden con la búsqueda."""
    def __init__(self, termino: str, opciones: List[Producto]):
        self.termino = termino
        self.opciones = opciones
        super().__init__(f"Búsqueda ambigua para '{termino}': {len(opciones)} productos encontrados")


class EstadoPresupuesto(str, Enum):
    """Estado general del cálculo de presupuesto."""
    OK = "ok"                           # Cálculo completado
    CATALOGO_DESCONECTADO = "catalogo_desconectado"
    CATALOGO_INACCESIBLE = "catalogo_inaccesible"
    PRESUPUESTO_EXCEDIDO = "presupuesto_excedido"
    ERROR = "error"


@dataclass
class ItemPresupuesto:
    """Un ítem en la lista de presupuesto."""
    # Identificación solicitada por el usuario
    termino_busqueda: str               # Lo que pidió el usuario: "arroz", "leche entera"
    cantidad: int = 1                   # Cantidad solicitada
    unidad: str = "unidad"              # Unidad: "unidad", "kg", "litro", "pack"

    # Resolución contra catálogo (llenado por el planner)
    producto: Optional[Producto] = None
    precio_info: Optional[PrecioInfo] = None
    stock_info: Optional[StockInfo] = None

    # Estado y cálculos
    estado: EstadoProductoPresupuesto = EstadoProductoPresupuesto.NO_ENCONTRADO
    precio_unitario: Decimal = Decimal("0")
    subtotal: Decimal = Decimal("0")
    mensaje: str = ""                   # Explicación para el usuario

    def __post_init__(self):
        # Asegurar Decimal
        if isinstance(self.precio_unitario, (int, float, str)):
            self.precio_unitario = Decimal(str(self.precio_unitario))
        if isinstance(self.subtotal, (int, float, str)):
            self.subtotal = Decimal(str(self.subtotal))
        # Calcular subtotal si hay precio y cantidad
        if self.precio_unitario > 0 and self.cantidad > 0:
            self.subtotal = (self.precio_unitario * self.cantidad).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a dict serializable (JSON)."""
        return {
            "termino_busqueda": self.termino_busqueda,
            "cantidad": self.cantidad,
            "unidad": self.unidad,
            "producto_id": self.producto.id if self.producto else None,
            "producto_nombre": self.producto.nombre if self.producto else None,
            "producto_imagen_url": self.producto.imagen_url if self.producto else None,
            "producto_sku": self.producto.sku if self.producto else None,
            "producto_marca": self.producto.marca if self.producto else None,
            "producto_presentacion": self.producto.presentacion if self.producto else None,
            "precio_unitario": float(self.precio_unitario),
            "subtotal": float(self.subtotal),
            "estado": self.estado.value,
            "mensaje": self.mensaje,
            "stock_disponible": self.stock_info.cantidad if self.stock_info else None,
            "tiene_promocion": self.precio_info.tiene_promocion if self.precio_info else False,
        }


@dataclass
class ResultadoPresupuesto:
    """Resultado completo del cálculo de presupuesto."""
    items: List[ItemPresupuesto] = field(default_factory=list)
    presupuesto_limite: Optional[Decimal] = None  # Presupuesto máximo del usuario

    # Totales calculados
    total_con_precio: Decimal = Decimal("0")      # Suma de items con precio conocido
    total_sin_precio: int = 0                      # Cantidad de items sin precio
    total_no_encontrados: int = 0                  # Cantidad de items no en catálogo
    total_sin_stock: int = 0                       # Cantidad de items sin disponibilidad

    # Estado global
    estado: EstadoPresupuesto = EstadoPresupuesto.OK
    mensaje: str = ""

    # Comparación con presupuesto
    presupuesto_excedido: bool = False
    diferencia_presupuesto: Decimal = Decimal("0")  # Positivo = sobra, Negativo = falta

    # Metadatos
    sede_id: Optional[str] = None
    catalogo_conectado: bool = True
    proveedor_usado: str = "desconocido"

    def __post_init__(self):
        if isinstance(self.presupuesto_limite, (int, float, str)):
            self.presupuesto_limite = Decimal(str(self.presupuesto_limite)) if self.presupuesto_limite else None
        if isinstance(self.total_con_precio, (int, float, str)):
            self.total_con_precio = Decimal(str(self.total_con_precio))
        if isinstance(self.diferencia_presupuesto, (int, float, str)):
            self.diferencia_presupuesto = Decimal(str(self.diferencia_presupuesto))

        # Recalcular comparativa si hay presupuesto límite
        if self.presupuesto_limite is not None:
            self.diferencia_presupuesto = self.presupuesto_limite - self.total_con_precio
            self.presupuesto_excedido = self.total_con_precio > self.presupuesto_limite
            if self.presupuesto_excedido and self.estado == EstadoPresupuesto.OK:
                self.estado = EstadoPresupuesto.PRESUPUESTO_EXCEDIDO

    @property
    def items_validos(self) -> List[ItemPresupuesto]:
        """Items con precio conocido y disponible."""
        return [i for i in self.items if i.estado == EstadoProductoPresupuesto.DISPONIBLE]

    @property
    def items_problematicos(self) -> List[ItemPresupuesto]:
        """Items con problemas (sin stock, sin precio, no encontrados)."""
        return [i for i in self.items if i.estado != EstadoProductoPresupuesto.DISPONIBLE]

    @property
    def resumen_usuario(self) -> str:
        """Resumen legible para mostrar al cliente."""
        lineas = []

        if self.presupuesto_limite:
            lineas.append(f"💰 Presupuesto: ${self._fmt(self.presupuesto_limite)} COP")

        lineas.append(f"🧮 Total calculado: ${self._fmt(self.total_con_precio)} COP")

        if self.presupuesto_limite:
            if self.presupuesto_excedido:
                lineas.append(f"⚠️ Te pasas por ${self._fmt(abs(self.diferencia_presupuesto))} COP")
            else:
                lineas.append(f"✅ Te quedan ${self._fmt(self.diferencia_presupuesto)} COP")

        if self.total_sin_stock > 0:
            lineas.append(f"📦 {self.total_sin_stock} producto(s) sin stock")
        if self.total_no_encontrados > 0:
            lineas.append(f"🔍 {self.total_no_encontrados} producto(s) no encontrados")
        if self.total_sin_precio > 0:
            lineas.append(f"❓ {self.total_sin_precio} producto(s) sin precio")

        return "\n".join(lineas)

    @staticmethod
    def _fmt(valor: Decimal) -> str:
        """Formato colombiano: puntos para miles."""
        return f"{valor:,.0f}".replace(",", ".")

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a dict serializable (JSON)."""
        return {
            "items": [item.to_dict() for item in self.items],
            "presupuesto_limite": float(self.presupuesto_limite) if self.presupuesto_limite else None,
            "total_con_precio": float(self.total_con_precio),
            "total_sin_precio": self.total_sin_precio,
            "total_no_encontrados": self.total_no_encontrados,
            "total_sin_stock": self.total_sin_stock,
            "estado": self.estado.value,
            "mensaje": self.mensaje,
            "presupuesto_excedido": self.presupuesto_excedido,
            "diferencia_presupuesto": float(self.diferencia_presupuesto),
            "sede_id": self.sede_id,
            "catalogo_conectado": self.catalogo_conectado,
            "proveedor_usado": self.proveedor_usado,
            "resumen_usuario": self.resumen_usuario,
        }


class BudgetPlanner:
    """
    Planificador de presupuesto - Cálculos comerciales puros.

    Responsabilidades:
    - Recibir lista de productos solicitados
    - Resolver contra catálogo (buscar productos)
    - Consultar precios y stock en lote (proveedor autoritativo)
    - Calcular subtotales y totales
    - Comparar con presupuesto del usuario
    - Devolver resultado tipado con estado detallado

    NO hace:
    - Generar lenguaje natural (eso es del LLM)
    - Tomar decisiones de compra
    - Guardar estado persistente (eso es del contexto conversacional)
    """

    def __init__(self, proveedor: ProductProvider):
        self.proveedor = proveedor
        self._ultimo_error: Optional[str] = None

    async def calcular_presupuesto(
        self,
        items_solicitados: List[Dict[str, Any]],
        presupuesto_limite: Optional[Decimal] = None,
        sede_id: Optional[str] = None
    ) -> ResultadoPresupuesto:
        """
        Calcula el presupuesto para una lista de productos solicitados.

        Args:
            items_solicitados: Lista de dicts con claves:
                - termino_busqueda (str): "arroz", "leche entera", etc.
                - cantidad (int, opcional): default 1
                - unidad (str, opcional): default "unidad"
            presupuesto_limite: Presupuesto máximo en COP (opcional)
            sede_id: Sede para consultar precios/stock (opcional)

        Returns:
            ResultadoPresupuesto con items resueltos, totales y estado
        """
        # Verificar estado del catálogo
        if catalogo_state.estado == CatalogoEstado.DESCONECTADO:
            return self._resultado_error(
                EstadoPresupuesto.CATALOGO_DESCONECTADO,
                "El catálogo está desconectado. No puedo consultar precios reales.",
                sede_id, presupuesto_limite
            )

        if catalogo_state.estado == CatalogoEstado.DEGRADADO:
            logger.warning(f"Catálogo degradado: {catalogo_state.ultimo_error}")

        # 1. Validar y normalizar items solicitados
        items = self._normalizar_items(items_solicitados)

        # 2. Resolver productos en catálogo (búsqueda)
        items = await self._resolver_productos(items, sede_id)

        # 3. Consultar precios en lote
        items = await self._consultar_precios_lote(items, sede_id)

        # 4. Consultar stock en lote
        items = await self._consultar_stock_lote(items, sede_id)

        # 5. Calcular subtotales y clasificar
        resultado = self._calcular_totales(items, presupuesto_limite, sede_id)

        return resultado

    def _normalizar_items(self, items_solicitados: List[Dict[str, Any]]) -> List[ItemPresupuesto]:
        """Valida y normaliza la lista de items solicitados."""
        items = []
        for idx, item in enumerate(items_solicitados):
            if not isinstance(item, dict):
                items.append(ItemPresupuesto(
                    termino_busqueda=str(item),
                    estado=EstadoProductoPresupuesto.ERROR_PROVEEDOR,
                    mensaje=f"Formato inválido en item {idx}"
                ))
                continue

            termino = item.get("termino_busqueda") or item.get("producto") or item.get("nombre", "")
            if not termino:
                items.append(ItemPresupuesto(
                    termino_busqueda=f"item_{idx}",
                    estado=EstadoProductoPresupuesto.ERROR_PROVEEDOR,
                    mensaje="Término de búsqueda vacío"
                ))
                continue

            try:
                cantidad = int(item.get("cantidad", 1))
                if cantidad <= 0:
                    cantidad = 1
            except (ValueError, TypeError):
                cantidad = 1

            unidad = str(item.get("unidad", "unidad")).strip() or "unidad"

            items.append(ItemPresupuesto(
                termino_busqueda=termino.strip(),
                cantidad=cantidad,
                unidad=unidad
            ))

        return items

    async def _resolver_productos(
        self,
        items: List[ItemPresupuesto],
        sede_id: Optional[str]
    ) -> List[ItemPresupuesto]:
        """Busca cada producto en el catálogo usando el proveedor."""
        for item in items:
            # Saltar items que ya tienen un estado de error (ej: término vacío, formato inválido)
            if item.estado != EstadoProductoPresupuesto.NO_ENCONTRADO:
                continue

            try:
                # Buscar en catálogo
                resultados = await self.proveedor.buscar(
                    item.termino_busqueda,
                    filtros=None,  # Sin filtros iniciales, el stock se verifica después
                    tipo_busqueda=None  # Usar default del proveedor
                )

                if not resultados:
                    item.estado = EstadoProductoPresupuesto.NO_ENCONTRADO
                    item.mensaje = f"No se encontró '{item.termino_busqueda}' en el catálogo"
                    continue

                # Detectar ambigüedad: múltiples resultados relevantes
                if len(resultados) > 1:
                    # Filtrar productos con stock > 0 si hay sede
                    productos_validos = resultados
                    if sede_id:
                        productos_validos = [p for p in resultados if p.stock_por_sede.get(sede_id, 0) > 0]

                    if len(productos_validos) > 1:
                        # Hay ambigüedad real - guardar opciones y marcar como ambiguo
                        item.estado = EstadoProductoPresupuesto.AMBIGUO
                        item.mensaje = (
                            f"Se encontraron {len(productos_validos)} productos para '{item.termino_busqueda}'. "
                            f"Opciones: {', '.join([f'{p.nombre} (${p.precio_final:,.0f})' for p in productos_validos[:3]])}"
                            f"{'...' if len(productos_validos) > 3 else ''}. "
                            f"Por favor especifica cuál deseas."
                        )
                        # Guardar las opciones en metadatos para que el agente las pueda presentar
                        item.producto = productos_validos[0]  # placeholder para no romper flujo
                        continue

                # Tomar el primer resultado (más relevante)
                producto = resultados[0]
                item.producto = producto
                item.estado = EstadoProductoPresupuesto.DISPONIBLE  # provisional, se confirmará con precio/stock

            except ProveedorNoDisponibleError as e:
                self._ultimo_error = str(e)
                item.estado = EstadoProductoPresupuesto.ERROR_PROVEEDOR
                item.mensaje = f"Catálogo no disponible: {e}"
            except Exception as e:
                logger.warning(f"Error buscando '{item.termino_busqueda}': {e}")
                item.estado = EstadoProductoPresupuesto.ERROR_PROVEEDOR
                item.mensaje = f"Error consultando catálogo"

        return items

    async def _consultar_precios_lote(
        self,
        items: List[ItemPresupuesto],
        sede_id: Optional[str]
    ) -> List[ItemPresupuesto]:
        """Consulta precios para todos los productos encontrados en una sola operación."""
        # Filtrar items que tienen producto resuelto
        items_con_producto = [i for i in items if i.producto is not None]
        if not items_con_producto:
            return items

        producto_ids = [i.producto.id for i in items_con_producto]

        try:
            precios = await self.proveedor.obtener_precios_lote(producto_ids, sede_id)

            for item in items_con_producto:
                precio_info = precios.get(item.producto.id)
                if precio_info and precio_info.precio_final > 0:
                    item.precio_info = precio_info
                    item.precio_unitario = Decimal(str(precio_info.precio_final))
                else:
                    item.estado = EstadoProductoPresupuesto.SIN_PRECIO
                    item.mensaje = f"'{item.termino_busqueda}' encontrado pero sin precio verificable"

        except ProveedorNoDisponibleError as e:
            self._ultimo_error = str(e)
            for item in items_con_producto:
                item.estado = EstadoProductoPresupuesto.ERROR_PROVEEDOR
                item.mensaje = "Error consultando precios"
        except Exception as e:
            logger.warning(f"Error consultando precios lote: {e}")
            for item in items_con_producto:
                if item.estado == EstadoProductoPresupuesto.DISPONIBLE:
                    item.estado = EstadoProductoPresupuesto.ERROR_PROVEEDOR
                    item.mensaje = "Error consultando precios"

        return items

    async def _consultar_stock_lote(
        self,
        items: List[ItemPresupuesto],
        sede_id: Optional[str]
    ) -> List[ItemPresupuesto]:
        """Consulta stock para todos los productos en una sola operación."""
        items_con_producto = [i for i in items if i.producto is not None and sede_id]
        if not items_con_producto:
            return items

        # Preparar items para stock: [(producto_id, sede_id), ...]
        items_stock = [(i.producto.id, sede_id) for i in items_con_producto]

        try:
            stocks = await self.proveedor.verificar_stock_lote(items_stock)

            for item in items_con_producto:
                key = f"{item.producto.id}:{sede_id}"
                stock_info = stocks.get(key)
                if stock_info:
                    item.stock_info = stock_info
                    if stock_info.cantidad <= 0:
                        item.estado = EstadoProductoPresupuesto.SIN_STOCK
                        item.mensaje = f"'{item.termino_busqueda}' sin stock en sede {sede_id}"

        except ProveedorNoDisponibleError as e:
            self._ultimo_error = str(e)
            for item in items_con_producto:
                item.estado = EstadoProductoPresupuesto.ERROR_PROVEEDOR
                item.mensaje = "Error consultando stock"
        except Exception as e:
            logger.warning(f"Error consultando stock lote: {e}")
            for item in items_con_producto:
                if item.estado == EstadoProductoPresupuesto.DISPONIBLE:
                    item.estado = EstadoProductoPresupuesto.ERROR_PROVEEDOR
                    item.mensaje = "Error consultando stock"

        return items

    def _calcular_totales(
        self,
        items: List[ItemPresupuesto],
        presupuesto_limite: Optional[Decimal],
        sede_id: Optional[str]
    ) -> ResultadoPresupuesto:
        """Calcula subtotales, totales y estado final."""
        total_con_precio = Decimal("0")
        total_sin_precio = 0
        total_no_encontrados = 0
        total_sin_stock = 0

        for item in items:
            if item.estado == EstadoProductoPresupuesto.DISPONIBLE and item.precio_unitario > 0:
                item.subtotal = (item.precio_unitario * item.cantidad).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
                total_con_precio += item.subtotal
            elif item.estado == EstadoProductoPresupuesto.SIN_PRECIO:
                total_sin_precio += 1
            elif item.estado == EstadoProductoPresupuesto.NO_ENCONTRADO:
                total_no_encontrados += 1
            elif item.estado == EstadoProductoPresupuesto.SIN_STOCK:
                total_sin_stock += 1
            elif item.estado == EstadoProductoPresupuesto.ERROR_PROVEEDOR:
                total_sin_precio += 1  # Contar como problema de precio

        # Determinar estado global
        estado = EstadoPresupuesto.OK
        mensaje = ""

        if catalogo_state.estado == CatalogoEstado.DESCONECTADO:
            estado = EstadoPresupuesto.CATALOGO_DESCONECTADO
            mensaje = "Catálogo desconectado - precios no verificables"
        elif catalogo_state.estado == CatalogoEstado.DEGRADADO:
            estado = EstadoPresupuesto.CATALOGO_INACCESIBLE
            mensaje = f"Catálogo degradado: {catalogo_state.ultimo_error}"
        elif self._ultimo_error:
            estado = EstadoPresupuesto.CATALOGO_INACCESIBLE
            mensaje = f"Error en proveedor: {self._ultimo_error}"

        resultado = ResultadoPresupuesto(
            items=items,
            presupuesto_limite=presupuesto_limite,
            total_con_precio=total_con_precio,
            total_sin_precio=total_sin_precio,
            total_no_encontrados=total_no_encontrados,
            total_sin_stock=total_sin_stock,
            estado=estado,
            mensaje=mensaje,
            sede_id=sede_id,
            catalogo_conectado=catalogo_state.estado == CatalogoEstado.CONECTADO,
            proveedor_usado=self.proveedor.nombre,
        )

        # La comparación con presupuesto se hace en __post_init__ de ResultadoPresupuesto
        if presupuesto_limite is not None:
            resultado.diferencia_presupuesto = presupuesto_limite - total_con_precio
            resultado.presupuesto_excedido = total_con_precio > presupuesto_limite
            if resultado.presupuesto_excedido and resultado.estado == EstadoPresupuesto.OK:
                resultado.estado = EstadoPresupuesto.PRESUPUESTO_EXCEDIDO

        return resultado

    def _resultado_error(
        self,
        estado: EstadoPresupuesto,
        mensaje: str,
        sede_id: Optional[str],
        presupuesto_limite: Optional[Decimal]
    ) -> ResultadoPresupuesto:
        """Crea un resultado de error sin items."""
        return ResultadoPresupuesto(
            items=[],
            presupuesto_limite=presupuesto_limite,
            total_con_precio=Decimal("0"),
            estado=estado,
            mensaje=mensaje,
            sede_id=sede_id,
            catalogo_conectado=False,
            proveedor_usado=self.proveedor.nombre,
        )

    # ==================== MÉTODOS DE CONVENIENCIA PARA EL AGENTE ====================

    async def calcular_lista_simple(
        self,
        terminos: List[str],
        presupuesto_limite: Optional[Decimal] = None,
        sede_id: Optional[str] = None
    ) -> ResultadoPresupuesto:
        """Versión simplificada: recibe lista de términos de búsqueda."""
        items = [{"termino_busqueda": t, "cantidad": 1} for t in terminos]
        return await self.calcular_presupuesto(items, presupuesto_limite, sede_id)

    async def recalcular_con_cambios(
        self,
        resultado_anterior: ResultadoPresupuesto,
        agregar: Optional[List[Dict[str, Any]]] = None,
        quitar: Optional[List[str]] = None,  # términos de búsqueda a quitar
        cambiar_cantidad: Optional[Dict[str, int]] = None,  # término -> nueva cantidad
        nuevo_presupuesto: Optional[Decimal] = None,
        sede_id: Optional[str] = None
    ) -> ResultadoPresupuesto:
        """
        Recalcula presupuesto aplicando cambios a una lista existente.
        Útil para mantener contexto conversacional.
        """
        # Reconstruir items desde resultado anterior
        items_actuales = []
        for item in resultado_anterior.items:
            termino = item.termino_busqueda

            # Verificar si se quita
            if quitar and termino in quitar:
                continue

            # Verificar cambio de cantidad
            cantidad = item.cantidad
            if cambiar_cantidad and termino in cambiar_cantidad:
                cantidad = cambiar_cantidad[termino]

            items_actuales.append({
                "termino_busqueda": termino,
                "cantidad": cantidad,
                "unidad": item.unidad
            })

        # Agregar nuevos
        if agregar:
            items_actuales.extend(agregar)

        # Recalcular con nuevo presupuesto si se proporciona
        presupuesto = nuevo_presupuesto if nuevo_presupuesto is not None else resultado_anterior.presupuesto_limite

        return await self.calcular_presupuesto(items_actuales, presupuesto, sede_id or resultado_anterior.sede_id)


# ==================== FUNCIONES DE FÁBRICA ====================

def crear_budget_planner(proveedor: ProductProvider) -> BudgetPlanner:
    """Factory para crear BudgetPlanner con proveedor inyectado."""
    return BudgetPlanner(proveedor)