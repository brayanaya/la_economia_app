"""
Comparison Engine - Motor de comparación inteligente de productos.

Compara productos usando datos reales del proveedor, normalizando unidades,
calculando precio por unidad base, y manejando disponibilidad por sede.
"""
from __future__ import annotations
import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from enum import Enum

from app.services.providers.base import (
    Producto, ProductProvider, FiltrosBusqueda, TipoBusqueda, PrecioInfo, StockInfo
)
from app.schemas.comparison import (
    TipoComparacion,
    ProductoComparacion,
    ResultadoComparacionItem,
    ComparacionResponse,
    SolicitudComparacion,
    normalizar_unidad,
    convertir_a_base,
    son_unidades_compatibles,
    CONVERSIONES_UNIDADES,
    UnidadMedida,
)

logger = logging.getLogger(__name__)


class EstadoComparacion(str, Enum):
    """Estados posibles de un producto en la comparación."""
    COMPARABLE = "comparable"
    INCOMPATIBLE_UNIDADES = "incompatible_unidades"
    SIN_STOCK = "sin_stock"
    SIN_PRECIO = "sin_precio"
    AMBIGUO = "ambiguo"  # No se puede determinar presentación


@dataclass
class ProductoAnalisis:
    """Producto con análisis interno para comparación."""
    producto_original: Producto
    producto_comparacion: ProductoComparacion
    estado: EstadoComparacion = EstadoComparacion.COMPARABLE
    precio_por_unidad_base: Optional[Decimal] = None
    unidad_base: Optional[UnidadMedida] = None
    cantidad_base: Optional[Decimal] = None
    advertencias: List[str] = field(default_factory=list)


class ComparisonEngine:
    """
    Motor de comparación inteligente de productos.

    Características:
    - Normalización de unidades (g/kg, ml/l, und/pack/docena)
    - Cálculo de precio por unidad base (COP/g, COP/ml, COP/und)
    - Comparación sede-aware (precios y stock por sede)
    - Detección de incompatibilidades (ej. g vs ml para productos de distinta densidad)
    - Explicación de limitaciones cuando la comparación no es justa
    - Uso de métodos batch del proveedor (obtener_precios_lote, verificar_stock_lote)
    """

    def __init__(self, proveedor: ProductProvider):
        """
        Inicializa el motor de comparación.

        Args:
            proveedor: Proveedor de productos que implementa ProductProvider
        """
        self.proveedor = proveedor

    async def comparar(
        self,
        solicitud: SolicitudComparacion,
        sede_id: Optional[str] = None
    ) -> ComparacionResponse:
        """
        Realiza una comparación inteligente de productos.

        Args:
            solicitud: Solicitud con términos de búsqueda y tipo de comparación
            sede_id: Sede opcional para filtrar precios/stock

        Returns:
            ComparacionResponse con análisis completo
        """
        sede_final = sede_id or solicitud.sede_id

        # 1. Buscar productos para cada término
        todos_productos = []
        for termino in solicitud.terminos_busqueda:
            filtros = FiltrosBusqueda(sede_id=sede_final, limite=10) if sede_final else FiltrosBusqueda(limite=10)
            productos = await self.proveedor.buscar(termino, filtros=filtros, tipo_busqueda=TipoBusqueda.TEXTO)
            todos_productos.extend(productos)

        # Deduplicar por SKU
        productos_unicos = {}
        for p in todos_productos:
            if p.sku not in productos_unicos:
                productos_unicos[p.sku] = p

        productos_lista = list(productos_unicos.values())

        if len(productos_lista) < 2:
            return ComparacionResponse(
                tipo_comparacion=solicitud.tipo_comparacion,
                criterio=self._describir_criterio(solicitud.tipo_comparacion),
                productos=[],
                explicacion="Se necesitan al menos 2 productos para comparar. "
                           f"Solo se encontraron {len(productos_lista)} productos.",
                limitaciones=["Pocos resultados de búsqueda"],
                sede_id=sede_final,
                comparables=False
            )

        # 2. Obtener precios y stock en lote (batch)
        # obtener_precios_lote espera producto_ids (no SKUs)
        producto_ids = [p.id for p in productos_lista]
        precios_dict = await self.proveedor.obtener_precios_lote(producto_ids, sede_id=sede_final)

        # verificar_stock_lote espera List[tuple[producto_id, sede_id]]
        stock_dict = {}
        if sede_final:
            stock_items = [(pid, sede_final) for pid in producto_ids]
            stock_dict_result = await self.proveedor.verificar_stock_lote(stock_items)
            stock_dict = {k: v.cantidad for k, v in stock_dict_result.items()}
        else:
            # Fallback: usar stock_total del producto o la primera sede en stock_por_sede
            for pid in producto_ids:
                producto = next((p for p in productos_lista if p.id == pid), None)
                if producto:
                    if producto.stock_total > 0:
                        stock_dict[pid] = producto.stock_total
                    elif producto.stock_por_sede:
                        stock_dict[pid] = next(iter(producto.stock_por_sede.values()))
                    else:
                        stock_dict[pid] = 0

        # 3. Analizar cada producto
        productos_analisis = []
        for producto in productos_lista:
            precio_info = precios_dict.get(producto.id)
            stock = stock_dict.get(producto.id, 0)
            analisis = self._analizar_producto(producto, precio_info, stock)
            productos_analisis.append(analisis)

        # 4. Detectar comparabilidad
        compatibles, limitaciones = self._evaluar_comparabilidad(productos_analisis)

        if not compatibles:
            # Aún así retornamos resultados pero marcamos como no comparables
            return self._construir_respuesta_no_comparable(
                productos_analisis,
                solicitud.tipo_comparacion,
                limitaciones,
                sede_final
            )

        # 5. Calcular puntuaciones según criterio (incluye todos los productos)
        items_resultado = self._calcular_puntuaciones(
            productos_analisis,
            solicitud.tipo_comparacion,
            solicitud.contexto_adicional
        )

        # 6. Determinar mejor opción
        mejor_opcion = max(items_resultado, key=lambda x: x.puntuacion).producto if items_resultado else None

        # 7. Generar explicación
        explicacion = self._generar_explicacion(
            items_resultado,
            solicitud.tipo_comparacion,
            solicitud.contexto_adicional
        )

        return ComparacionResponse(
            tipo_comparacion=solicitud.tipo_comparacion,
            criterio=self._describir_criterio(solicitud.tipo_comparacion),
            productos=items_resultado,
            mejor_opcion=mejor_opcion,
            explicacion=explicacion,
            limitaciones=limitaciones,
            sede_id=sede_final,
            comparables=True
        )

    def _analizar_producto(
        self,
        producto: Producto,
        precio_info: Optional[PrecioInfo],
        stock: int
    ) -> ProductoAnalisis:
        """Analiza un producto individual extrayendo y normalizando sus datos."""
        # Extraer precio desde PrecioInfo
        precio_final = Decimal("0")
        precio_base = None
        tiene_promocion = False
        promocion_descripcion = None

        if precio_info:
            precio_final = Decimal(str(precio_info.precio_final))
            if precio_info.precio_base and precio_info.precio_base > 0:
                precio_base = Decimal(str(precio_info.precio_base))
                if precio_base > precio_final:
                    tiene_promocion = True
                    promocion_descripcion = precio_info.promocion_descripcion or "Promoción aplicada"
            # Si el producto ya tiene precio_final/precio_base, usarlos como fallback
            elif producto.precio_final > 0:
                precio_final = Decimal(str(producto.precio_final))
                if producto.precio_base and producto.precio_base > precio_final:
                    precio_base = Decimal(str(producto.precio_base))
                    tiene_promocion = True
                    promocion_descripcion = "Promoción aplicada"

        # Extraer unidad y contenido neto del producto
        unidad_medida = producto.unidad_medida
        contenido_neto = producto.contenido_neto

        # Si no hay unidad en el producto, intentar extraer del nombre/presentación
        if not unidad_medida or not contenido_neto:
            unidad_extraida, contenido_extraido = self._extraer_unidad_y_contenido(
                producto.nombre,
                producto.presentacion
            )
            if unidad_extraida and contenido_extraido:
                unidad_medida = unidad_extraida
                contenido_neto = contenido_extraido

        # Convertir a unidad base
        cantidad_base = None
        precio_por_unidad_base = None
        unidad_base = None
        advertencias = []

        if unidad_medida and contenido_neto is not None and contenido_neto > 0:
            cantidad_base = convertir_a_base(Decimal(str(contenido_neto)), unidad_medida)
            if cantidad_base and cantidad_base > 0:
                unidad_base = normalizar_unidad(unidad_medida)
                precio_por_unidad_base = (precio_final / cantidad_base).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                advertencias.append("No se pudo determinar cantidad base")
        else:
            # Intentar inferir si es unidad simple
            if producto.unidad_medida and any(u in producto.unidad_medida.lower() for u in ["und", "unidad", "unidades", "u"]):
                unidad_base = UnidadMedida.UNIDAD
                cantidad_base = Decimal("1")
                precio_por_unidad_base = precio_final
            else:
                advertencias.append("Unidad de medida no reconocida o no especificada")

        # Verificar stock
        disponible = stock > 0
        if not disponible:
            advertencias.append("Sin stock en la sede consultada")

        # Crear objeto de comparación
        producto_comparacion = ProductoComparacion(
            id=str(producto.id),
            sku=producto.sku,
            nombre=producto.nombre,
            marca=producto.marca,
            presentacion=producto.presentacion,
            imagen_url=producto.imagen_url,
            precio_final=float(precio_final),
            precio_base=float(precio_base) if precio_base else None,
            tiene_promocion=tiene_promocion,
            promocion_descripcion=promocion_descripcion,
            unidad_medida=unidad_medida,
            contenido_neto=float(contenido_neto) if contenido_neto else None,
            stock=stock,
            disponible=disponible,
            sede_id=producto.stock_por_sede.keys().__iter__().__next__() if producto.stock_por_sede else None,
            precio_por_unidad_base=float(precio_por_unidad_base) if precio_por_unidad_base else None
        )

        # Determinar estado
        estado = EstadoComparacion.COMPARABLE
        if not disponible:
            estado = EstadoComparacion.SIN_STOCK
        elif precio_final <= 0:
            estado = EstadoComparacion.SIN_PRECIO
        elif not unidad_base:
            estado = EstadoComparacion.AMBIGUO
        elif precio_por_unidad_base is None:
            estado = EstadoComparacion.INCOMPATIBLE_UNIDADES

        return ProductoAnalisis(
            producto_original=producto,
            producto_comparacion=producto_comparacion,
            estado=estado,
            precio_por_unidad_base=precio_por_unidad_base,
            unidad_base=unidad_base,
            cantidad_base=cantidad_base,
            advertencias=advertencias
        )

    def _extraer_unidad_y_contenido(
        self,
        nombre: str,
        presentacion: Optional[str]
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Extrae unidad de medida y contenido neto del nombre y presentación.

        Patrones comunes:
        - "Aceite 900ml" -> ("ml", 900)
        - "Arroz x 1kg" -> ("kg", 1)
        - "Leche 1L" -> ("l", 1)
        - "Huevos x 12" -> ("und", 12) o ("doc", 1)
        - "Pasta 500g" -> ("g", 500)
        """
        texto = f"{nombre} {presentacion or ''}".lower()

        # Patrones: número + unidad (con o sin separador)
        patrones = [
            # kg, g
            (r"(\d+(?:[.,]\d+)?)\s*(kg|kilos?|kilogramos?)", "kg"),
            (r"(\d+(?:[.,]\d+)?)\s*(g|gr|gramos?)", "g"),
            # l, ml
            (r"(\d+(?:[.,]\d+)?)\s*(l|lt|litros?)", "l"),
            (r"(\d+(?:[.,]\d+)?)\s*(ml|mililitros?)", "ml"),
            # unidades
            (r"(\d+(?:[.,]\d+)?)\s*(und|unidades?|u\b)", "und"),
            (r"(\d+(?:[.,]\d+)?)\s*(pack|paquetes?|paq)", "pack"),
            (r"(pack|paquetes?|paq)\s*(\d+(?:[.,]\d+)?)", "pack"),  # "pack 6" format
            (r"(\d+(?:[.,]\d+)?)\s*(doc|docenas?)", "doc"),
            # Formato "x N" (ej: "x 12", "x 6")
            (r"x\s*(\d+(?:[.,]\d+)?)", None),  # Unidad se infiere del contexto
        ]

        for patron, unidad_forzada in patrones:
            match = re.search(patron, texto)
            if match:
                # Para patrones como "pack 6", el número está en group(2)
                if "pack" in patron and "pack" in match.group(0).lower() and match.lastindex >= 2:
                    # Verificar si group(1) es "pack" y group(2) es el número
                    if match.group(1).lower() in ["pack", "paquete", "paquetes", "paq"]:
                        cantidad_str = match.group(2).replace(",", ".")
                    else:
                        cantidad_str = match.group(1).replace(",", ".")
                else:
                    cantidad_str = match.group(1).replace(",", ".")
                try:
                    cantidad = float(cantidad_str)
                    unidad = unidad_forzada
                    if not unidad:
                        # Inferir unidad del contexto
                        if any(p in texto for p in ["huevo", "huevos"]):
                            unidad = "und"
                        elif any(p in texto for p in ["lata", "latas", "tarro", "tarros", "frasco", "frascos"]):
                            unidad = "und"
                        else:
                            unidad = "und"  # Default
                    return unidad, cantidad
                except ValueError:
                    continue

        # Buscar en presentacion específicamente
        if presentacion:
            for unidad_key in CONVERSIONES_UNIDADES:
                if unidad_key in presentacion.lower():
                    # Intentar extraer número anterior
                    patron = rf"(\d+(?:[.,]\d+)?)\s*{re.escape(unidad_key)}"
                    match = re.search(patron, presentacion.lower())
                    if match:
                        return unidad_key, float(match.group(1).replace(",", "."))

        return None, None

    def _evaluar_comparabilidad(
        self,
        productos: List[ProductoAnalisis]
    ) -> Tuple[bool, List[str]]:
        """
        Evalúa si los productos son comparables entre sí.

        Returns:
            (son_comparables, lista_limitaciones)
        """
        limitaciones = []

        # Filtrar productos con estado válido
        validos = [p for p in productos if p.estado == EstadoComparacion.COMPARABLE]

        if len(validos) < 2:
            # Verificar razones
            sin_stock = [p for p in productos if p.estado == EstadoComparacion.SIN_STOCK]
            ambiguos = [p for p in productos if p.estado == EstadoComparacion.AMBIGUO]
            incompatibles = [p for p in productos if p.estado == EstadoComparacion.INCOMPATIBLE_UNIDADES]
            sin_precio = [p for p in productos if p.estado == EstadoComparacion.SIN_PRECIO]

            if sin_stock:
                limitaciones.append(f"{len(sin_stock)} producto(s) sin stock")
            if ambiguos:
                limitaciones.append(f"{len(ambiguos)} producto(s) con presentación ambigua")
            if incompatibles:
                limitaciones.append(f"{len(incompatibles)} producto(s) con unidades incompatibles")
            if sin_precio:
                limitaciones.append(f"{len(sin_precio)} producto(s) sin precio")

            return False, limitaciones

        # Verificar compatibilidad de unidades entre productos válidos
        unidades_base = set(p.unidad_base for p in validos if p.unidad_base)

        if len(unidades_base) > 1:
            # Verificar si son dimensiones compatibles
            primera = next(iter(unidades_base))
            compatibles = all(
                son_unidades_compatibles(primera.value, u.value)
                for u in unidades_base
            )
            if not compatibles:
                limitaciones.append(
                    "Productos con unidades de distinta dimensión (ej. peso vs volumen). "
                    "La comparación por precio unitario no es justa."
                )
                return False, limitaciones
            else:
                limitaciones.append(
                    "Unidades diferentes pero compatibles (ej. g y kg). "
                    "Se ha normalizado a unidad base para comparación."
                )

        # Advertir si hay productos con promociones mixtas
        con_promo = [p for p in validos if p.producto_comparacion.tiene_promocion]
        sin_promo = [p for p in validos if not p.producto_comparacion.tiene_promocion]
        if con_promo and sin_promo:
            limitaciones.append(
                "Algunos productos tienen promoción y otros no. "
                "La comparación usa precio final (con promoción aplicada)."
            )

        return True, limitaciones

    def _construir_respuesta_no_comparable(
        self,
        productos: List[ProductoAnalisis],
        tipo: TipoComparacion,
        limitaciones: List[str],
        sede_id: Optional[str]
    ) -> ComparacionResponse:
        """Construye respuesta cuando los productos no son totalmente comparables."""
        items = []
        for p in productos:
            razones = []
            if p.estado == EstadoComparacion.SIN_STOCK:
                razones.append("Sin stock disponible")
            elif p.estado == EstadoComparacion.AMBIGUO:
                razones.append("Presentación no clara - no se puede calcular precio por unidad")
            elif p.estado == EstadoComparacion.INCOMPATIBLE_UNIDADES:
                razones.append("Unidad de medida incompatible para comparación justa")
            elif p.estado == EstadoComparacion.SIN_PRECIO:
                razones.append("Sin precio disponible")

            items.append(ResultadoComparacionItem(
                producto=p.producto_comparacion,
                puntuacion=0,
                razones=razones,
                advertencias=p.advertencias
            ))

        return ComparacionResponse(
            tipo_comparacion=tipo,
            criterio=self._describir_criterio(tipo),
            productos=items,
            explicacion="No se puede realizar una comparación justa: " + "; ".join(limitaciones),
            limitaciones=limitaciones,
            sede_id=sede_id,
            comparables=False
        )

    def _calcular_puntuaciones(
        self,
        productos: List[ProductoAnalisis],
        tipo: TipoComparacion,
        contexto: Optional[str]
    ) -> List[ResultadoComparacionItem]:
        """Calcula puntuaciones para cada producto según el criterio."""
        # Separar productos comparables y no comparables
        validos = [p for p in productos if p.estado == EstadoComparacion.COMPARABLE]
        no_comparables = [p for p in productos if p.estado != EstadoComparacion.COMPARABLE]

        items = []

        # Calcular puntuaciones para productos comparables
        if validos:
            if tipo == TipoComparacion.PRECIO_TOTAL:
                items_validos = self._puntuar_precio_total(validos)
            elif tipo == TipoComparacion.PRECIO_POR_UNIDAD:
                items_validos = self._puntuar_precio_por_unidad(validos)
            elif tipo == TipoComparacion.CANTIDAD:
                items_validos = self._puntuar_cantidad(validos)
            elif tipo == TipoComparacion.RELACION_PRECIO_CANTIDAD:
                items_validos = self._puntuar_relacion_precio_cantidad(validos)
            elif tipo == TipoComparacion.DISPONIBILIDAD:
                items_validos = self._puntuar_disponibilidad(validos)
            else:  # COMPLETA
                items_validos = self._puntuar_completa(validos, contexto)
            items.extend(items_validos)

        # Agregar productos no comparables con puntuación 0 y razones
        for p in no_comparables:
            razones = []
            if p.estado == EstadoComparacion.SIN_STOCK:
                razones.append("Sin stock disponible")
            elif p.estado == EstadoComparacion.AMBIGUO:
                razones.append("Presentación no clara - no se puede calcular precio por unidad")
            elif p.estado == EstadoComparacion.INCOMPATIBLE_UNIDADES:
                razones.append("Unidad de medida incompatible para comparación justa")
            elif p.estado == EstadoComparacion.SIN_PRECIO:
                razones.append("Sin precio disponible")

            items.append(ResultadoComparacionItem(
                producto=p.producto_comparacion,
                puntuacion=0,
                razones=razones,
                advertencias=p.advertencias
            ))

        return items

    def _puntuar_precio_total(self, productos: List[ProductoAnalisis]) -> List[ResultadoComparacionItem]:
        """Menor precio total = mejor puntuación."""
        precios = [Decimal(str(p.producto_comparacion.precio_final)) for p in productos]
        min_precio = min(precios)
        max_precio = max(precios)
        rango = max_precio - min_precio if max_precio != min_precio else Decimal("1")

        items = []
        for p in productos:
            precio = Decimal(str(p.producto_comparacion.precio_final))
            # Invertir: menor precio = mayor puntuación
            puntuacion = float(100 * (1 - (precio - min_precio) / rango))
            razones = [f"Precio total: ${precio:,.0f} COP"]
            if p.producto_comparacion.tiene_promocion:
                razones.append(f"Incluye promoción: {p.producto_comparacion.promocion_descripcion}")
            items.append(ResultadoComparacionItem(
                producto=p.producto_comparacion,
                puntuacion=round(puntuacion, 1),
                razones=razones,
                advertencias=p.advertencias
            ))
        return items

    def _puntuar_precio_por_unidad(self, productos: List[ProductoAnalisis]) -> List[ResultadoComparacionItem]:
        """Menor precio por unidad base = mejor puntuación."""
        precios_unit = [p.precio_por_unidad_base for p in productos if p.precio_por_unidad_base]
        if not precios_unit:
            return []

        min_precio = min(precios_unit)
        max_precio = max(precios_unit)
        rango = max_precio - min_precio if max_precio != min_precio else Decimal("1")

        items = []
        for p in productos:
            if p.precio_por_unidad_base is None:
                items.append(ResultadoComparacionItem(
                    producto=p.producto_comparacion,
                    puntuacion=0,
                    razones=["No se pudo calcular precio por unidad"],
                    advertencias=p.advertencias + ["Unidad base no disponible"]
                ))
                continue

            precio = p.precio_por_unidad_base
            puntuacion = float(100 * (1 - (precio - min_precio) / rango))
            unidad_str = p.unidad_base.value if p.unidad_base else "unidad"
            razones = [f"Precio por {unidad_str}: ${precio:,.2f} COP"]
            if p.cantidad_base:
                razones.append(f"Presentación: {p.cantidad_base} {unidad_str}")
            if p.producto_comparacion.tiene_promocion:
                razones.append(f"Promoción: {p.producto_comparacion.promocion_descripcion}")
            items.append(ResultadoComparacionItem(
                producto=p.producto_comparacion,
                puntuacion=round(puntuacion, 1),
                razones=razones,
                advertencias=p.advertencias
            ))
        return items

    def _puntuar_cantidad(self, productos: List[ProductoAnalisis]) -> List[ResultadoComparacionItem]:
        """Mayor cantidad por precio = mejor puntuación (más producto por tu dinero)."""
        # Calcular cantidad total por producto
        cantidades = []
        for p in productos:
            if p.cantidad_base and p.producto_comparacion.precio_final > 0:
                cant_por_peso = p.cantidad_base / Decimal(str(p.producto_comparacion.precio_final))
                cantidades.append(cant_por_peso)
            else:
                cantidades.append(Decimal("0"))

        max_cant = max(cantidades)
        min_cant = min(cantidades)
        rango = max_cant - min_cant if max_cant != min_cant else Decimal("1")

        items = []
        for p, cant in zip(productos, cantidades):
            if cant == 0:
                puntuacion = 0
                razones = ["No se pudo calcular cantidad por precio"]
            else:
                puntuacion = float(100 * (cant - min_cant) / rango)
                unidad_str = p.unidad_base.value if p.unidad_base else "unidades"
                razones = [f"Obtienes {cant:.4f} {unidad_str} por $1 COP"]
            items.append(ResultadoComparacionItem(
                producto=p.producto_comparacion,
                puntuacion=round(puntuacion, 1),
                razones=razones,
                advertencias=p.advertencias
            ))
        return items

    def _puntuar_relacion_precio_cantidad(self, productos: List[ProductoAnalisis]) -> List[ResultadoComparacionItem]:
        """Mejor relación precio-cantidad (equilibrio)."""
        # Usar precio por unidad como métrica principal
        return self._puntuar_precio_por_unidad(productos)

    def _puntuar_disponibilidad(self, productos: List[ProductoAnalisis]) -> List[ResultadoComparacionItem]:
        """Prioriza productos con stock disponible."""
        items = []
        for p in productos:
            if p.producto_comparacion.disponible:
                puntuacion = 100
                razones = [f"Disponible: {p.producto_comparacion.stock} unidades en stock"]
            else:
                puntuacion = 0
                razones = ["Sin stock en la sede consultada"]
            items.append(ResultadoComparacionItem(
                producto=p.producto_comparacion,
                puntuacion=puntuacion,
                razones=razones,
                advertencias=p.advertencias
            ))
        return items

    def _puntuar_completa(
        self,
        productos: List[ProductoAnalisis],
        contexto: Optional[str]
    ) -> List[ResultadoComparacionItem]:
        """
        Análisis completo combinando múltiples factores:
        - Precio por unidad (40%)
        - Disponibilidad (20%)
        - Promociones (15%)
        - Cantidad total (15%)
        - Contexto adicional (10%)
        """
        # Obtener puntuaciones base
        items_precio = {item.producto.id: item.puntuacion for item in self._puntuar_precio_por_unidad(productos)}
        items_disp = {item.producto.id: item.puntuacion for item in self._puntuar_disponibilidad(productos)}
        items_cant = {item.producto.id: item.puntuacion for item in self._puntuar_cantidad(productos)}

        # Promociones: bonus si tiene promo
        promo_scores = {}
        for p in productos:
            promo_scores[p.producto_comparacion.id] = 100 if p.producto_comparacion.tiene_promocion else 50

        # Contexto: ajustar según uso sugerido
        contexto_scores = {}
        if contexto:
            contexto_lower = contexto.lower()
            for p in productos:
                score = 50  # neutral
                nombre_lower = p.producto_comparacion.nombre.lower()
                marca_lower = (p.producto_comparacion.marca or "").lower()

                # Heurísticas simples por contexto
                if "freir" in contexto_lower or "frit" in contexto_lower:
                    if any(kw in nombre_lower for kw in ["aceite", "girasol", "maiz", "canola", "vegetal"]):
                        score = 100
                elif "ensalada" in contexto_lower:
                    if any(kw in nombre_lower for kw in ["oliva", "extra virgen", "virgen extra"]):
                        score = 100
                elif "hornear" in contexto_lower or "postre" in contexto_lower:
                    if any(kw in nombre_lower for kw in ["mantequilla", "margarina", "harina", "azucar"]):
                        score = 80
                contexto_scores[p.producto_comparacion.id] = score
        else:
            for p in productos:
                contexto_scores[p.producto_comparacion.id] = 50

        items = []
        for p in productos:
            pid = p.producto_comparacion.id
            puntuacion = (
                0.40 * items_precio.get(pid, 0) +
                0.20 * items_disp.get(pid, 0) +
                0.15 * promo_scores.get(pid, 50) +
                0.15 * items_cant.get(pid, 0) +
                0.10 * contexto_scores.get(pid, 50)
            )

            razones = []
            if p.precio_por_unidad_base:
                unidad_str = p.unidad_base.value if p.unidad_base else "unidad"
                razones.append(f"Precio/{unidad_str}: ${p.precio_por_unidad_base:,.2f}")
            if p.producto_comparacion.disponible:
                razones.append(f"Stock: {p.producto_comparacion.stock} und")
            if p.producto_comparacion.tiene_promocion:
                razones.append(f"Promo: {p.producto_comparacion.promocion_descripcion}")
            if contexto:
                razones.append(f"Para: {contexto}")

            items.append(ResultadoComparacionItem(
                producto=p.producto_comparacion,
                puntuacion=round(puntuacion, 1),
                razones=razones,
                advertencias=p.advertencias
            ))

        return items

    def _describir_criterio(self, tipo: TipoComparacion) -> str:
        """Descripción legible del criterio de comparación."""
        descripciones = {
            TipoComparacion.PRECIO_TOTAL: "Menor precio total",
            TipoComparacion.PRECIO_POR_UNIDAD: "Menor precio por unidad base (kg, l, und)",
            TipoComparacion.CANTIDAD: "Mayor cantidad por peso colombiano",
            TipoComparacion.RELACION_PRECIO_CANTIDAD: "Mejor relación precio-cantidad",
            TipoComparacion.DISPONIBILIDAD: "Priorizar productos con stock",
            TipoComparacion.COMPLETA: "Análisis integral (precio unitario, stock, promo, cantidad, contexto)"
        }
        return descripciones.get(tipo, "Criterio personalizado")

    def _generar_explicacion(
        self,
        items: List[ResultadoComparacionItem],
        tipo: TipoComparacion,
        contexto: Optional[str]
    ) -> str:
        """Genera explicación en lenguaje natural de los resultados."""
        if not items:
            return "No hay productos para comparar."

        mejor = max(items, key=lambda x: x.puntuacion)
        peor = min(items, key=lambda x: x.puntuacion)

        partes = []

        if tipo == TipoComparacion.PRECIO_POR_UNIDAD:
            partes.append(
                f"La mejor opción por precio unitario es **{mejor.producto.nombre}** "
                f"(${mejor.producto.precio_por_unidad_base:,.0f} COP/{mejor.producto.unidad_medida or 'und'})."
            )
        elif tipo == TipoComparacion.PRECIO_TOTAL:
            partes.append(
                f"El producto más económico en precio total es **{mejor.producto.nombre}** "
                f"(${mejor.producto.precio_final:,.0f} COP)."
            )
        elif tipo == TipoComparacion.COMPLETA:
            partes.append(
                f"Considerando precio por unidad, disponibilidad, promociones y "
                f"{f'contexto ({contexto})' if contexto else 'cantidad'}, "
                f"la mejor opción es **{mejor.producto.nombre}** (puntuación: {mejor.puntuacion}/100)."
            )
        else:
            partes.append(f"Según el criterio seleccionado, la mejor opción es **{mejor.producto.nombre}**.")

        # Diferencia con la peor opción
        if mejor.puntuacion > peor.puntuacion and len(items) > 1:
            diff = mejor.puntuacion - peor.puntuacion
            if diff > 20:
                partes.append(f"Hay una diferencia significativa ({diff:.0f} puntos) con la opción menos favorable.")
            elif diff > 10:
                partes.append(f"Hay una diferencia moderada ({diff:.0f} puntos) con la opción menos favorable.")

        # Mencionar promociones si hay
        con_promo = [i for i in items if i.producto.tiene_promocion]
        if con_promo:
            partes.append(f"{len(con_promo)} producto(s) tienen promoción activa.")

        # Mencionar stock
        sin_stock = [i for i in items if not i.producto.disponible]
        if sin_stock:
            partes.append(f"⚠️ {len(sin_stock)} producto(s) no tienen stock en la sede consultada.")

        return " ".join(partes)

    async def comparar_productos_seleccionados(
        self,
        sku_list: List[str],
        tipo: TipoComparacion = TipoComparacion.COMPLETA,
        sede_id: Optional[str] = None,
        contexto: Optional[str] = None
    ) -> ComparacionResponse:
        """
        Compara una lista específica de SKUs (útil cuando el usuario ya seleccionó productos).
        """
        productos = []
        for sku in sku_list:
            # Buscar por SKU exacto
            producto = await self.proveedor.obtener_por_sku(sku)
            if producto:
                productos.append(producto)

        if len(productos) < 2:
            return ComparacionResponse(
                tipo_comparacion=tipo,
                criterio=self._describir_criterio(tipo),
                productos=[],
                explicacion="Se necesitan al menos 2 productos válidos para comparar.",
                limitaciones=["Productos no encontrados o insuficientes"],
                sede_id=sede_id,
                comparables=False
            )

        # Usar los IDs de los productos encontrados
        producto_ids = [p.id for p in productos]

        # Obtener precios y stock
        precios_dict = await self.proveedor.obtener_precios_lote(producto_ids, sede_id=sede_id)
        if sede_id:
            stock_items = [(pid, sede_id) for pid in producto_ids]
            stock_dict_result = await self.proveedor.verificar_stock_lote(stock_items)
            stock_dict = {k: v.cantidad for k, v in stock_dict_result.items()}
        else:
            stock_dict = {}

        # Analizar
        productos_analisis = []
        for producto in productos:
            precio_info = precios_dict.get(producto.id)
            stock = stock_dict.get(producto.id, 0)
            analisis = self._analizar_producto(producto, precio_info, stock)
            productos_analisis.append(analisis)

        # Evaluar comparabilidad
        compatibles, limitaciones = self._evaluar_comparabilidad(productos_analisis)

        if not compatibles:
            return self._construir_respuesta_no_comparable(
                productos_analisis, tipo, limitaciones, sede_id
            )

        # Calcular puntuaciones
        items_resultado = self._calcular_puntuaciones(productos_analisis, tipo, contexto)
        mejor_opcion = max(items_resultado, key=lambda x: x.puntuacion).producto if items_resultado else None
        explicacion = self._generar_explicacion(items_resultado, tipo, contexto)

        return ComparacionResponse(
            tipo_comparacion=tipo,
            criterio=self._describir_criterio(tipo),
            productos=items_resultado,
            mejor_opcion=mejor_opcion,
            explicacion=explicacion,
            limitaciones=limitaciones,
            sede_id=sede_id,
            comparables=True
        )

    def formatear_para_agente(self, respuesta: ComparacionResponse) -> str:
        """
        Formatea la comparación para que el agente la incluya en su respuesta conversacional.
        """
        if not respuesta.productos:
            return respuesta.explicacion

        lineas = [respuesta.explicacion, ""]
        lineas.append("**Comparación detallada:**")

        for i, item in enumerate(respuesta.productos, 1):
            p = item.producto
            estado_emoji = "✅" if p.disponible else "❌"
            promo_emoji = " 🏷️" if p.tiene_promocion else ""

            linea = f"{i}. {estado_emoji} **{p.nombre}**{promo_emoji}"
            if p.marca:
                linea += f" ({p.marca})"
            if p.presentacion:
                linea += f" - {p.presentacion}"
            linea += f": ${p.precio_final:,.0f} COP"

            if p.precio_por_unidad_base and p.unidad_medida:
                linea += f" = ${p.precio_por_unidad_base:,.0f} COP/{p.unidad_medida}"

            if not p.disponible:
                linea += " (SIN STOCK)"

            lineas.append(linea)

            if item.razones:
                lineas.append(f"   └ {', '.join(item.razones)}")

        if respuesta.limitaciones:
            lineas.append("")
            lineas.append("⚠️ **Limitaciones:**")
            for lim in respuesta.limitaciones:
                lineas.append(f"   • {lim}")

        return "\n".join(lineas)