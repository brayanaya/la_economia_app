"""
Schemas para el Comparison Engine - Comparación inteligente de productos.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal
from enum import Enum


class TipoComparacion(str, Enum):
    """Tipos de comparación soportados."""
    PRECIO_TOTAL = "precio_total"
    PRECIO_POR_UNIDAD = "precio_por_unidad"
    CANTIDAD = "cantidad"
    RELACION_PRECIO_CANTIDAD = "relacion_precio_cantidad"
    DISPONIBILIDAD = "disponibilidad"
    COMPLETA = "completa"  # Análisis completo con todos los factores


class UnidadMedida(str, Enum):
    """Unidades de medida estandarizadas."""
    GRAMO = "g"
    KILOGRAMO = "kg"
    MILILITRO = "ml"
    LITRO = "l"
    UNIDAD = "und"
    PAQUETE = "pack"
    DOCINA = "doc"
    CENTIMETRO = "cm"
    METRO = "m"


class ProductoComparacion(BaseModel):
    """Producto en una comparación."""
    id: str
    sku: str
    nombre: str
    marca: Optional[str] = None
    presentacion: Optional[str] = None
    imagen_url: Optional[str] = None
    precio_final: float
    precio_base: Optional[float] = None
    tiene_promocion: bool = False
    promocion_descripcion: Optional[str] = None
    unidad_medida: Optional[str] = None
    contenido_neto: Optional[float] = None  # Cantidad en unidad base
    stock: int = 0
    disponible: bool = True
    sede_id: Optional[str] = None
    precio_por_unidad_base: Optional[float] = None  # Precio normalizado por kg/l/und


class ResultadoComparacionItem(BaseModel):
    """Un item en el resultado de comparación."""
    producto: ProductoComparacion
    puntuacion: float  # 0-100, mayor = mejor opción según criterio
    razones: List[str] = []  # Explicaciones de la puntuación
    advertencias: List[str] = []  # Limitaciones o problemas


class ComparacionResponse(BaseModel):
    """Respuesta completa de una comparación."""
    tipo_comparacion: TipoComparacion
    criterio: str  # Descripción legible del criterio usado
    productos: List[ResultadoComparacionItem]
    mejor_opcion: Optional[ProductoComparacion] = None
    explicacion: str = ""
    limitaciones: List[str] = []
    sede_id: Optional[str] = None
    comparables: bool = True  # False si no se puede comparar justamente


class SolicitudComparacion(BaseModel):
    """Solicitud para comparar productos."""
    terminos_busqueda: List[str] = Field(..., min_length=2, max_length=10)
    tipo_comparacion: TipoComparacion = TipoComparacion.COMPLETA
    sede_id: Optional[str] = None
    contexto_adicional: Optional[str] = None  # "para freir", "para ensalada", etc.


class ComparacionProductoSeleccionado(BaseModel):
    """Resultado cuando el usuario selecciona un producto de la comparación."""
    producto_id: str
    producto_nombre: str
    accion_sugerida: Literal["agregar_presupuesto", "agregar_carrito", "ver_detalles"]
    cantidad_sugerida: int = 1
    mensaje_confirmacion: str


# Constantes para conversión de unidades
CONVERSIONES_UNIDADES = {
    # Masa
    "g": (UnidadMedida.GRAMO, Decimal("1")),
    "gr": (UnidadMedida.GRAMO, Decimal("1")),
    "gramo": (UnidadMedida.GRAMO, Decimal("1")),
    "gramos": (UnidadMedida.GRAMO, Decimal("1")),
    "kg": (UnidadMedida.KILOGRAMO, Decimal("1000")),
    "kilo": (UnidadMedida.KILOGRAMO, Decimal("1000")),
    "kilogramo": (UnidadMedida.KILOGRAMO, Decimal("1000")),
    "kilogramos": (UnidadMedida.KILOGRAMO, Decimal("1000")),

    # Volumen
    "ml": (UnidadMedida.MILILITRO, Decimal("1")),
    "mililitro": (UnidadMedida.MILILITRO, Decimal("1")),
    "mililitros": (UnidadMedida.MILILITRO, Decimal("1")),
    "l": (UnidadMedida.LITRO, Decimal("1000")),
    "lt": (UnidadMedida.LITRO, Decimal("1000")),
    "litro": (UnidadMedida.LITRO, Decimal("1000")),
    "litros": (UnidadMedida.LITRO, Decimal("1000")),

    # Unidades
    "und": (UnidadMedida.UNIDAD, Decimal("1")),
    "unidad": (UnidadMedida.UNIDAD, Decimal("1")),
    "unidades": (UnidadMedida.UNIDAD, Decimal("1")),
    "u": (UnidadMedida.UNIDAD, Decimal("1")),
    "pack": (UnidadMedida.PAQUETE, Decimal("1")),
    "paquete": (UnidadMedida.PAQUETE, Decimal("1")),
    "paq": (UnidadMedida.PAQUETE, Decimal("1")),
    "docena": (UnidadMedida.DOCINA, Decimal("12")),
    "doc": (UnidadMedida.DOCINA, Decimal("12")),

    # Longitud (menos común en alimentos)
    "cm": (UnidadMedida.CENTIMETRO, Decimal("1")),
    "m": (UnidadMedida.METRO, Decimal("100")),
}


def normalizar_unidad(unidad: str) -> Optional[UnidadMedida]:
    """Normaliza una unidad de medida a su forma estándar."""
    unidad_lower = unidad.lower().strip()
    if unidad_lower in CONVERSIONES_UNIDADES:
        return CONVERSIONES_UNIDADES[unidad_lower][0]
    return None


def convertir_a_base(cantidad: Decimal, unidad: str) -> Optional[Decimal]:
    """Convierte una cantidad en su unidad a la unidad base (g, ml, und)."""
    unidad_lower = unidad.lower().strip()
    if unidad_lower in CONVERSIONES_UNIDADES:
        _, factor = CONVERSIONES_UNIDADES[unidad_lower]
        return cantidad * factor
    return None


def son_unidades_compatibles(unidad1: str, unidad2: str) -> bool:
    """Verifica si dos unidades son compatibles (misma dimensión)."""
    u1 = normalizar_unidad(unidad1)
    u2 = normalizar_unidad(unidad2)
    if not u1 or not u2:
        return False

    # Mismo tipo de dimensión
    masa = {UnidadMedida.GRAMO, UnidadMedida.KILOGRAMO}
    volumen = {UnidadMedida.MILILITRO, UnidadMedida.LITRO}
    cuenta = {UnidadMedida.UNIDAD, UnidadMedida.PAQUETE, UnidadMedida.DOCINA}

    return (u1 in masa and u2 in masa) or \
           (u1 in volumen and u2 in volumen) or \
           (u1 in cuenta and u2 in cuenta)