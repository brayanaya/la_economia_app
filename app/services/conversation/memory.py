"""
Gestión de memoria contextual para conversaciones con el agente IA.

Proporciona:
- Historial de conversación por sesión
- Referencias a productos mencionados
- Contexto de recetas discutidas
- Límites de tokens y caducidad
- Protección de datos personales (Ley 1581)
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class RolMensaje(str, Enum):
    USUARIO = "user"
    ASISTENTE = "assistant"
    SISTEMA = "system"


@dataclass
class MensajeConversacion:
    """Un mensaje en la conversación."""
    rol: RolMensaje
    contenido: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Metadatos opcionales para contexto
    productos_mencionados: List[str] = field(default_factory=list)  # IDs de productos
    receta_id: Optional[str] = None
    intencion: Optional[str] = None
    acciones_sugeridas: List[Dict[str, Any]] = field(default_factory=list)  # Ej: {"tipo": "agregar_carrito", "producto_id": "..."}


@dataclass
class ContextoConversacion:
    """Contexto persistente de una conversación."""
    conversacion_id: str
    usuario_id: Optional[str] = None
    mensajes: List[MensajeConversacion] = field(default_factory=list)
    # Contexto semántico
    productos_recientes: List[str] = field(default_factory=list)  # Últimos productos mencionados
    receta_actual: Optional[str] = None
    lista_mercado_actual: List[Dict[str, Any]] = field(default_factory=list)
    presupuesto_actual: Optional[Union[float, Any]] = None  # float o ResultadoPresupuesto
    sede_preferida: Optional[str] = None
    # Metadatos
    creada_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actualizada_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    mensaje_count: int = 0

    def agregar_mensaje(self, mensaje: MensajeConversacion):
        """Agrega mensaje y actualiza contexto semántico."""
        self.mensajes.append(mensaje)
        self.mensaje_count += 1
        self.actualizada_en = datetime.now(timezone.utc)

        # Actualizar contexto semántico
        if mensaje.productos_mencionados:
            # Mantener últimos 10 productos únicos
            for pid in mensaje.productos_mencionados:
                if pid in self.productos_recientes:
                    self.productos_recientes.remove(pid)
                self.productos_recientes.insert(0, pid)
            self.productos_recientes = self.productos_recientes[:10]

        if mensaje.receta_id:
            self.receta_actual = mensaje.receta_id

        if mensaje.intencion == "lista_mercado" and mensaje.acciones_sugeridas:
            for accion in mensaje.acciones_sugeridas:
                if accion.get("tipo") == "agregar_lista":
                    self.lista_mercado_actual.append(accion)

    def obtener_historial_para_llm(self, limite: int = 10) -> List[Dict[str, str]]:
        """Retorna historial formateado para LLM (últimos N mensajes)."""
        recientes = self.mensajes[-limite:] if self.mensajes else []
        return [
            {"role": m.rol.value, "content": m.contenido}
            for m in recientes
        ]

    def obtener_contexto_resumido(self) -> str:
        """Genera un resumen textual del contexto para el prompt."""
        partes = []

        if self.receta_actual:
            partes.append(f"Receta en contexto: {self.receta_actual}")

        if self.productos_recientes:
            partes.append(f"Productos recientes: {', '.join(self.productos_recientes[:5])}")

        if self.lista_mercado_actual:
            items = [f"{i.get('cantidad', 1)}x {i.get('producto', 'item')}" for i in self.lista_mercado_actual[:5]]
            partes.append(f"Lista de mercado: {', '.join(items)}")

        if self.presupuesto_actual:
            # Manejar tanto float (legacy) como ResultadoPresupuesto (nuevo)
            if hasattr(self.presupuesto_actual, 'total_con_precio'):
                # Es un ResultadoPresupuesto
                total = self.presupuesto_actual.total_con_precio
                limite = self.presupuesto_actual.presupuesto_limite
                if limite is not None:
                    partes.append(f"Presupuesto: ${total:,.0f} / ${limite:,.0f} COP")
                else:
                    partes.append(f"Presupuesto calculado: ${total:,.0f} COP")
            else:
                # Es un float (legacy)
                partes.append(f"Presupuesto: ${self.presupuesto_actual:,.0f} COP")

        if self.sede_preferida:
            partes.append(f"Sede preferida: {self.sede_preferida}")

        return " | ".join(partes) if partes else "Conversación nueva"

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para almacenamiento (Redis, BD, etc.)."""
        return {
            "conversacion_id": self.conversacion_id,
            "usuario_id": self.usuario_id,
            "mensajes": [
                {
                    "rol": m.rol.value,
                    "contenido": m.contenido,
                    "timestamp": m.timestamp.isoformat(),
                    "productos_mencionados": m.productos_mencionados,
                    "receta_id": m.receta_id,
                    "intencion": m.intencion,
                    "acciones_sugeridas": m.acciones_sugeridas,
                }
                for m in self.mensajes
            ],
            "productos_recientes": self.productos_recientes,
            "receta_actual": self.receta_actual,
            "lista_mercado_actual": self.lista_mercado_actual,
            "presupuesto_actual": self.presupuesto_actual,
            "sede_preferida": self.sede_preferida,
            "creada_en": self.creada_en.isoformat(),
            "actualizada_en": self.actualizada_en.isoformat(),
            "mensaje_count": self.mensaje_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextoConversacion":
        """Deserializa desde almacenamiento."""
        mensajes = [
            MensajeConversacion(
                rol=RolMensaje(m["rol"]),
                contenido=m["contenido"],
                timestamp=datetime.fromisoformat(m["timestamp"]),
                productos_mencionados=m.get("productos_mencionados", []),
                receta_id=m.get("receta_id"),
                intencion=m.get("intencion"),
                acciones_sugeridas=m.get("acciones_sugeridas", []),
            )
            for m in data.get("mensajes", [])
        ]

        ctx = cls(
            conversacion_id=data["conversacion_id"],
            usuario_id=data.get("usuario_id"),
            mensajes=mensajes,
            productos_recientes=data.get("productos_recientes", []),
            receta_actual=data.get("receta_actual"),
            lista_mercado_actual=data.get("lista_mercado_actual", []),
            presupuesto_actual=data.get("presupuesto_actual"),
            sede_preferida=data.get("sede_preferida"),
            creada_en=datetime.fromisoformat(data["creada_en"]),
            actualizada_en=datetime.fromisoformat(data["actualizada_en"]),
            mensaje_count=data.get("mensaje_count", 0),
        )
        return ctx


class ConversationMemoryManager:
    """
    Gestor de memoria conversacional.

    En producción debería usar Redis con TTL.
    En desarrollo usa diccionario en memoria.
    """

    def __init__(self, max_historial: int = 20, ttl_minutos: int = 60):
        self._memoria: Dict[str, ContextoConversacion] = {}
        self.max_historial = max_historial
        self.ttl = timedelta(minutes=ttl_minutos)

    def _limpiar_expirados(self):
        """Limpia conversaciones expiradas."""
        ahora = datetime.now(timezone.utc)
        expirados = [
            cid for cid, ctx in self._memoria.items()
            if ahora - ctx.actualizada_en > self.ttl
        ]
        for cid in expirados:
            del self._memoria[cid]

    def obtener_o_crear(self, conversacion_id: Optional[str] = None, usuario_id: Optional[str] = None) -> ContextoConversacion:
        """Obtiene conversación existente o crea nueva."""
        self._limpiar_expirados()

        if conversacion_id and conversacion_id in self._memoria:
            return self._memoria[conversacion_id]

        # Nueva conversación
        nuevo_id = conversacion_id or str(uuid.uuid4())
        ctx = ContextoConversacion(conversacion_id=nuevo_id, usuario_id=usuario_id)
        self._memoria[nuevo_id] = ctx
        return ctx

    def guardar(self, contexto: ContextoConversacion):
        """Guarda/actualiza conversación."""
        self._memoria[contexto.conversacion_id] = contexto

    def eliminar(self, conversacion_id: str) -> bool:
        """Elimina una conversación (derecho al olvido - Ley 1581)."""
        if conversacion_id in self._memoria:
            del self._memoria[conversacion_id]
            return True
        return False

    def obtener_todas_usuario(self, usuario_id: str) -> List[ContextoConversacion]:
        """Obtiene todas las conversaciones de un usuario (para exportación Ley 1581)."""
        return [ctx for ctx in self._memoria.values() if ctx.usuario_id == usuario_id]

    def limpiar_usuario(self, usuario_id: str) -> int:
        """Elimina todas las conversaciones de un usuario (supresión Ley 1581)."""
        count = 0
        for cid in list(self._memoria.keys()):
            if self._memoria[cid].usuario_id == usuario_id:
                del self._memoria[cid]
                count += 1
        return count


# Instancia global (en producción: Redis)
conversation_memory = ConversationMemoryManager()


def get_conversation_memory() -> ConversationMemoryManager:
    """Dependency injection para FastAPI."""
    return conversation_memory