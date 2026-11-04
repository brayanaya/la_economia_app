"""
Interfaz base (Protocol) para proveedores de catálogo.

Define el contrato que deben implementar todos los proveedores:
- MockProvider (desarrollo/testing)
- MasControlProvider (producción)
- Futuro providers (otros ERPs, APIs, etc.)

Esto permite que la IA sea agnóstica a la fuente de datos.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol, Optional, List, Dict, Any, Literal
from uuid import UUID
import uuid


class TipoBusqueda(str, Enum):
    """Tipos de búsqueda soportados."""
    SEMANTICA = "semantica"           # Por embeddings/vector similarity
    TEXTO = "texto"                   # Full-text / ILIKE
    EXACTA = "exacta"                 # Por ID/SKU/EAN exacto
    CATEGORIA = "categoria"           # Por categoría
    RECETA = "receta"                 # Ingredientes de receta
    PRESUPUESTO = "presupuesto"       # Optimizar por presupuesto


@dataclass
class FiltrosBusqueda:
    """Filtros comunes para búsquedas de productos."""
    sede_id: Optional[str] = None
    categoria_id: Optional[str] = None
    solo_con_stock: bool = True
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    marcas: Optional[List[str]] = None
    etiquetas: Optional[List[str]] = None  # "promocion", "nuevo", "organico", etc.
    limite: int = 20
    offset: int = 0
    ordenar_por: Literal["relevancia", "precio_asc", "precio_desc", "popularidad", "novedad"] = "relevancia"


@dataclass
class StockInfo:
    """Información de stock por sede."""
    producto_id: str
    sede_id: str
    cantidad: int
    disponible: bool
    reservado: int = 0
    en_camino: int = 0
    actualizado_en: Optional[datetime] = None


@dataclass
class PrecioInfo:
    """Información de precio (puede variar por sede, cliente, promociones)."""
    producto_id: str
    sede_id: Optional[str] = None
    precio_base: float = 0.0
    precio_final: float = 0.0
    moneda: str = "COP"
    tiene_promocion: bool = False
    promocion_id: Optional[str] = None
    promocion_descripcion: Optional[str] = None
    precio_por_unidad: Optional[float] = None  # Para comparar presentaciones
    unidad_medida: Optional[str] = None  # "kg", "unidad", "litro", etc.


@dataclass
class Producto:
    """
    Producto normalizado - contrato común entre proveedores.
    Todos los proveedores deben retornar instancias de esta clase.
    """
    id: str
    sku: str
    nombre: str
    descripcion: Optional[str] = None
    descripcion_corta: Optional[str] = None
    categoria_id: Optional[str] = None
    categoria_nombre: Optional[str] = None
    marca: Optional[str] = None
    imagen_url: Optional[str] = None
    imagenes_adicionales: List[str] = field(default_factory=list)
    # Precios (se llenan via obtener_precio)
    precio_base: float = 0.0
    precio_final: float = 0.0
    tiene_promocion: bool = False
    # Stock (se llena via verificar_stock)
    stock_total: int = 0
    stock_por_sede: Dict[str, int] = field(default_factory=dict)
    # Metadatos
    unidad_medida: Optional[str] = None  # "kg", "g", "ml", "l", "unidad", "pack"
    contenido_neto: Optional[float] = None  # ej: 500 (gr/ml)
    presentacion: Optional[str] = None  # "Bolsa x500g", "Botella 1.5L", "Pack x6"
    codigo_barras: Optional[str] = None  # EAN13
    etiquetas: List[str] = field(default_factory=list)  # ["promocion", "organico", "sin_gluten", "nuevo"]
    # Para IA/recetas
    ingredientes_receta: List[str] = field(default_factory=list)  # Nombres de ingredientes que aporta
    # Origen de datos (CRÍTICO para distinguir mock vs real)
    fuente: str = "desconocido"  # "fixture_desarrollo", "mascontrol", "api_externa"
    fecha_actualizacion: Optional[datetime] = None
    # Campos extra flexibles
    metadatos: Dict[str, Any] = field(default_factory=dict)

    @property
    def precio_por_unidad_base(self) -> Optional[float]:
        """Precio por unidad base (kg, litro, unidad) para comparativas."""
        if self.contenido_neto and self.contenido_neto > 0 and self.precio_final > 0:
            return self.precio_final / self.contenido_neto
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a dict para API/JSON."""
        return {
            "id": self.id,
            "sku": self.sku,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "descripcion_corta": self.descripcion_corta,
            "categoria_id": self.categoria_id,
            "categoria_nombre": self.categoria_nombre,
            "marca": self.marca,
            "imagen_url": self.imagen_url,
            "imagenes_adicionales": self.imagenes_adicionales,
            "precio_base": self.precio_base,
            "precio_final": self.precio_final,
            "tiene_promocion": self.tiene_promocion,
            "stock_total": self.stock_total,
            "stock_por_sede": self.stock_por_sede,
            "unidad_medida": self.unidad_medida,
            "contenido_neto": self.contenido_neto,
            "presentacion": self.presentacion,
            "codigo_barras": self.codigo_barras,
            "etiquetas": self.etiquetas,
            "ingredientes_receta": self.ingredientes_receta,
            "fuente": self.fuente,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            "metadatos": self.metadatos,
        }


@dataclass
class ComparacionCriterio:
    """Criterio para comparar productos."""
    producto_ids: List[str]
    sede_id: Optional[str] = None
    incluir_precio_por_unidad: bool = True
    incluir_stock: bool = True
    incluir_promociones: bool = True
    incluir_valoraciones: bool = False  # Futuro: ratings/reviews


@dataclass
class ComparacionResultado:
    """Resultado de comparativa entre productos."""
    productos: List[Producto]
    mejor_precio: Optional[Producto] = None
    mejor_precio_por_unidad: Optional[Producto] = None
    mejor_disponibilidad: Optional[Producto] = None
    resumen: str = ""


@dataclass
class Promocion:
    """Promoción activa."""
    id: str
    nombre: str
    descripcion: str
    tipo: Literal["descuento_porcentaje", "descuento_fijo", "lleva_x_paga_y", "precio_especial", "bundling"]
    valor: float  # % descuento, valor fijo, etc.
    productos_ids: List[str]
    fecha_inicio: datetime
    fecha_fin: datetime
    categorias_ids: List[str] = field(default_factory=list)
    sede_ids: List[str] = field(default_factory=list)  # Vacío = todas
    activa: bool = True
    metadatos: Dict[str, Any] = field(default_factory=dict)


class ProductProvider(Protocol):
    """
    Protocolo que define la interfaz obligatoria para cualquier proveedor de catálogo.

    Implementaciones:
    - MockProvider: Usa fixtures locales para desarrollo
    - MasControlProvider: Conecta a MasControl ERP (producción)
    - HybridProvider: Combina múltiples fuentes con prioridad
    """

    # ==================== INFORMACIÓN DEL PROVEEDOR ====================

    @property
    def nombre(self) -> str:
        """Nombre identificador del proveedor: 'mock', 'mascontrol', etc."""
        ...

    @property
    def version(self) -> str:
        """Versión del proveedor/esquema."""
        ...

    @property
    def esta_disponible(self) -> bool:
        """True si el proveedor está operativo (conexión OK, credenciales válidas)."""
        ...

    async def health_check(self) -> Dict[str, Any]:
        """Verifica estado de conexión y retorna info de diagnóstico."""
        ...

    # ==================== BÚSQUEDA Y LISTADO ====================

    async def buscar(
        self,
        query: str,
        filtros: Optional[FiltrosBusqueda] = None,
        tipo_busqueda: TipoBusqueda = TipoBusqueda.SEMANTICA
    ) -> List[Producto]:
        """
        Busca productos según query y filtros.

        Args:
            query: Texto de búsqueda (puede ser lenguaje natural, SKU, ingredientes)
            filtros: Filtros opcionales (sede, categoría, precio, stock, etc.)
            tipo_busqueda: Estrategia de búsqueda a usar

        Returns:
            Lista de productos ordenados por relevancia
        """
        ...

    async def obtener_por_id(self, producto_id: str) -> Optional[Producto]:
        """Obtiene un producto por su ID único."""
        ...

    async def obtener_por_sku(self, sku: str) -> Optional[Producto]:
        """Obtiene un producto por SKU."""
        ...

    async def obtener_por_codigo_barras(self, ean13: str) -> Optional[Producto]:
        """Obtiene un producto por código de barras EAN13."""
        ...

    async def listar_por_categoria(
        self,
        categoria_id: str,
        filtros: Optional[FiltrosBusqueda] = None
    ) -> List[Producto]:
        """Lista productos de una categoría."""
        ...

    async def listar_novedades(self, limite: int = 10, sede_id: Optional[str] = None) -> List[Producto]:
        """Productos recién agregados."""
        ...

    async def listar_mas_vendidos(
        self,
        periodo_dias: int = 30,
        limite: int = 10,
        sede_id: Optional[str] = None
    ) -> List[Producto]:
        """Productos más vendidos en un período."""
        ...

    # ==================== PRECIOS Y STOCK ====================

    async def obtener_precio(
        self,
        producto_id: str,
        sede_id: Optional[str] = None,
        cliente_id: Optional[str] = None  # Para precios personalizados futuros
    ) -> PrecioInfo:
        """Obtiene información completa de precio para un producto en una sede."""
        ...

    async def obtener_precios_lote(
        self,
        producto_ids: List[str],
        sede_id: Optional[str] = None
    ) -> Dict[str, PrecioInfo]:
        """Obtiene precios para múltiples productos de una vez (batch)."""
        ...

    async def verificar_stock(
        self,
        producto_id: str,
        sede_id: str
    ) -> StockInfo:
        """Verifica stock real-time de un producto en una sede."""
        ...

    async def verificar_stock_lote(
        self,
        items: List[tuple[str, str]]  # [(producto_id, sede_id), ...]
    ) -> Dict[str, StockInfo]:
        """Verifica stock para múltiples items de una vez."""
        ...

    # ==================== COMPARATIVAS Y RECOMENDACIONES ====================

    async def comparar_productos(self, criterio: ComparacionCriterio) -> ComparacionResultado:
        """
        Compara productos según criterio (precio, stock, promociones, etc.).
        Útil para que la IA recomende "la mejor opción".
        """
        ...

    async def obtener_alternativas(
        self,
        producto_id: str,
        limite: int = 5,
        sede_id: Optional[str] = None
    ) -> List[Producto]:
        """Productos alternativos/similares (misma categoría, precio similar, etc.)."""
        ...

    async def obtener_complementos(
        self,
        producto_id: str,
        limite: int = 5
    ) -> List[Producto]:
        """Productos que se suelen comprar juntos (cross-sell)."""
        ...

    # ==================== PROMOCIONES ====================

    async def obtener_promociones_activas(
        self,
        sede_id: Optional[str] = None,
        categoria_id: Optional[str] = None
    ) -> List[Promocion]:
        """Promociones vigentes."""
        ...

    async def obtener_promociones_producto(
        self,
        producto_id: str,
        sede_id: Optional[str] = None
    ) -> List[Promocion]:
        """Promociones que aplican a un producto específico."""
        ...

    # ==================== RECETAS / INGREDIENTES ====================

    async def buscar_ingredientes_receta(
        self,
        ingredientes: List[str],
        sede_id: Optional[str] = None,
        presupuesto_max: Optional[float] = None
    ) -> Dict[str, List[Producto]]:
        """
        Para cada ingrediente de una receta, busca los mejores productos.
        Retorna dict: {ingrediente: [productos_ordenados]}
        """
        ...

    async def calcular_costo_receta(
        self,
        ingredientes: List[Dict[str, Any]],  # [{ingrediente, cantidad, unidad}, ...]
        sede_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calcula costo total de una receta buscando mejores precios.
        Retorna: {total, por_ingrediente, productos_seleccionados, ahorro_vs_promedio}
        """
        ...

    # ==================== SINCRONIZACIÓN (solo proveedores reales) ====================

    async def sincronizar_catalogo_completo(self) -> Dict[str, Any]:
        """Sincronización completa (full sync) - solo para proveedores reales."""
        ...

    async def sincronizar_incremental(self, desde: datetime) -> Dict[str, Any]:
        """Sincronización incremental (delta sync) - solo para proveedores reales."""
        ...

    async def obtener_ultima_sincronizacion(self) -> Optional[datetime]:
        """Timestamp de última sincronización exitosa."""
        ...


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class ProveedorError(Exception):
    """Error base del proveedor."""
    def __init__(self, mensaje: str, proveedor: str, codigo: str = "PROVEEDOR_ERROR"):
        self.proveedor = proveedor
        self.codigo = codigo
        super().__init__(mensaje)


class ProveedorNoDisponibleError(ProveedorError):
    """El proveedor no está disponible (caído, sin credenciales, etc.)."""
    def __init__(self, proveedor: str, detalle: str = ""):
        super().__init__(f"Proveedor {proveedor} no disponible: {detalle}", proveedor, "NO_DISPONIBLE")


class ProveedorTimeoutError(ProveedorError):
    """Timeout en llamada al proveedor."""
    def __init__(self, proveedor: str, operacion: str):
        super().__init__(f"Timeout en {proveedor}.{operacion}", proveedor, "TIMEOUT")


class ProductoNoEncontradoError(ProveedorError):
    """Producto no existe en el proveedor."""
    def __init__(self, proveedor: str, producto_id: str):
        super().__init__(f"Producto {producto_id} no encontrado en {proveedor}", proveedor, "NO_ENCONTRADO")


class SincronizacionError(ProveedorError):
    """Error durante sincronización de catálogo."""
    def __init__(self, proveedor: str, detalle: str):
        super().__init__(f"Error sincronización {proveedor}: {detalle}", proveedor, "SINC_ERROR")