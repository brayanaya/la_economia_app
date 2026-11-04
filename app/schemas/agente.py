from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict, Literal
import uuid


# ============================================================
# CART ACTIONS - Tipos para acciones de carrito desde el agente
# ============================================================

class CartActionItem(BaseModel):
    """Item para acción de carrito."""
    producto_id: str
    nombre: str
    cantidad: int = Field(ge=1, le=99)
    precio_unitario: float
    sede_id: str
    imagen_url: Optional[str] = None


class CartActionAdd(BaseModel):
    """Acción: agregar productos al carrito."""
    tipo: Literal["add"] = "add"
    items: List[CartActionItem]


class CartActionRemove(BaseModel):
    """Acción: quitar productos del carrito."""
    tipo: Literal["remove"] = "remove"
    producto_ids: List[str]
    sede_id: str


class CartActionUpdate(BaseModel):
    """Acción: actualizar cantidad de productos en el carrito."""
    tipo: Literal["update"] = "update"
    items: List[CartActionItem]


class CartActionClear(BaseModel):
    """Acción: vaciar carrito (por sede o todo)."""
    tipo: Literal["clear"] = "clear"
    sede_id: Optional[str] = None


class CartActionConfirmClear(BaseModel):
    """Acción: solicitar confirmación para vaciar carrito."""
    tipo: Literal["confirm_clear"] = "confirm_clear"
    sede_id: Optional[str] = None
    mensaje: str = "¿Estás seguro de que quieres vaciar el carrito? Esta acción no se puede deshacer."


class CartActionList(BaseModel):
    """Acción: listar contenido del carrito."""
    tipo: Literal["list"] = "list"
    sede_id: Optional[str] = None


class CartActionResponse(BaseModel):
    """Respuesta de acción de carrito."""
    tipo: Literal["add", "remove", "update", "clear", "list"]
    exitoso: bool
    mensaje: str
    items: Optional[List[CartActionItem]] = None
    total_items: Optional[int] = None
    total_precio: Optional[float] = None
    error: Optional[str] = None


# Union type for all cart actions
CartAction = CartActionAdd | CartActionRemove | CartActionUpdate | CartActionClear | CartActionList | CartActionConfirmClear


class AgenteChatRequest(BaseModel):
    mensaje: str = Field(..., min_length=2, max_length=500)
    sede_id: uuid.UUID | None = Field(
        default=None, description="Si se especifica, filtra disponibilidad por stock en esa sede."
    )
    # Conversation context for memory
    conversacion_id: Optional[str] = Field(
        default=None, description="ID de conversación para mantener contexto"
    )
    historial: Optional[List[dict]] = Field(
        default=None, description="Historial de mensajes previos [{\"role\": \"user|assistant\", \"content\": \"...\"}]"
    )
    # Budget planning fields
    presupuesto: Optional[float] = Field(
        default=None, description="Presupuesto máximo en COP para cálculo de lista de mercado"
    )
    lista_mercado: Optional[List[dict]] = Field(
        default=None, description="Lista explícita de items: [{termino_busqueda, cantidad, unidad}]"
    )


class RecetaIngredienteResponse(BaseModel):
    nombre: str
    cantidad: str
    busqueda_catalogo: str
    obligatorio: bool
    notas: str = ""


class RecetaResponse(BaseModel):
    id: str
    nombre: str
    descripcion: str
    categoria: str
    tiempo_min: int
    porciones: int
    costo_estimado_cop: float
    imagen_url: Optional[str] = None
    ingredientes: list[RecetaIngredienteResponse]
    pasos: list[str]
    tags: list[str]


class CatalogoEstadoResponse(BaseModel):
    estado: str
    conectado: bool
    modo_mock: bool
    ultimo_error: Optional[str] = None
    mensaje_usuario: str


class PresupuestoItemResponse(BaseModel):
    termino_busqueda: str
    cantidad: int
    unidad: str
    producto_id: Optional[str] = None
    producto_nombre: Optional[str] = None
    producto_imagen_url: Optional[str] = None
    precio_unitario: float
    subtotal: float
    estado: str  # disponible, sin_stock, sin_precio, no_encontrado, error_proveedor
    mensaje: str = ""


class PresupuestoResponse(BaseModel):
    items: List[PresupuestoItemResponse] = []
    presupuesto_limite: Optional[float] = None
    total_con_precio: float = 0
    total_sin_precio: int = 0
    total_no_encontrados: int = 0
    total_sin_stock: int = 0
    estado: str = "ok"
    mensaje: str = ""
    presupuesto_excedido: bool = False
    diferencia_presupuesto: float = 0
    sede_id: Optional[str] = None
    catalogo_conectado: bool = True
    proveedor_usado: str = "desconocido"
    resumen_usuario: str = ""


class ComparacionItemResponse(BaseModel):
    """Item simplificado de comparación para respuesta del agente."""
    id: str
    sku: str
    nombre: str
    marca: Optional[str] = None
    presentacion: Optional[str] = None
    precio_final: float
    precio_por_unidad_base: Optional[float] = None
    unidad_medida: Optional[str] = None
    stock: int
    disponible: bool
    tiene_promocion: bool = False
    puntuacion: float
    razones: List[str] = []


class ComparacionResponse(BaseModel):
    """Respuesta de comparación para el agente."""
    tipo_comparacion: str
    criterio: str
    productos: List[ComparacionItemResponse]
    mejor_opcion_id: Optional[str] = None
    explicacion: str = ""
    limitaciones: List[str] = []
    sede_id: Optional[str] = None
    comparables: bool = True


class AgenteChatResponse(BaseModel):
    mensaje: str
    respuesta: str
    productos_recomendados: list[Any]
    hubo_resultados_relevantes: bool
    receta: Optional[RecetaResponse] = None
    estado_catalogo: Optional[CatalogoEstadoResponse] = None
    conversacion_id: Optional[str] = None
    generado_por_llm: bool = False
    # Budget planning response
    presupuesto: Optional[PresupuestoResponse] = None
    # Comparison response
    comparacion: Optional[ComparacionResponse] = None
    # Cart actions
    cart_actions: Optional[List[CartAction]] = None