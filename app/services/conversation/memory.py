"""
Gestión de memoria contextual para conversaciones con el agente IA (PostgreSQL).

Proporciona:
- Historial de conversación por sesión (persistente en BD)
- Referencias a productos mencionados
- Contexto de recetas discutidas
- Resumen automático para conversaciones largas
- Límites de tokens y control de contexto
- Protección de datos personales (Ley 1581 Colombia)
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from sqlalchemy import select, func, delete, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, NoResultFound
from fastapi import Depends

from app.models.conversacion import Conversacion, Mensaje, TipoRemitente

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
    productos_mencionados: List[str] = field(default_factory=list)
    receta_id: Optional[str] = None
    intencion: Optional[str] = None
    acciones_sugeridas: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ContextoConversacion:
    """Contexto persistente de una conversación."""
    conversacion_id: str
    usuario_id: Optional[str] = None
    mensajes: List[MensajeConversacion] = field(default_factory=list)
    # Contexto semántico (sincronizado con BD)
    productos_recientes: List[str] = field(default_factory=list)
    receta_actual: Optional[str] = None
    lista_mercado_actual: List[Dict[str, Any]] = field(default_factory=list)
    presupuesto_actual: Optional[Union[float, Any]] = None
    sede_preferida: Optional[str] = None
    # Resumen automático
    resumen: Optional[str] = None
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
            if hasattr(self.presupuesto_actual, 'total_con_precio'):
                total = self.presupuesto_actual.total_con_precio
                limite = self.presupuesto_actual.presupuesto_limite
                if limite is not None:
                    partes.append(f"Presupuesto: ${total:,.0f} / ${limite:,.0f} COP")
                else:
                    partes.append(f"Presupuesto calculado: ${total:,.0f} COP")
            else:
                partes.append(f"Presupuesto: ${self.presupuesto_actual:,.0f} COP")

        if self.sede_preferida:
            partes.append(f"Sede preferida: {self.sede_preferida}")

        return " | ".join(partes) if partes else "Conversación nueva"

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para almacenamiento."""
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
            "resumen": self.resumen,
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
            resumen=data.get("resumen"),
            creada_en=datetime.fromisoformat(data["creada_en"]),
            actualizada_en=datetime.fromisoformat(data["actualizada_en"]),
            mensaje_count=data.get("mensaje_count", 0),
        )
        return ctx


# Umbral para activar resumen automático (número de mensajes)
RESUMEN_UMBRAL_MENSAJES = 20
# Máximo mensajes en historial para LLM (evitar exceder context window)
MAX_HISTORIAL_LLM = 10
# ID de usuario por defecto para usuarios anónimos/invitados
DEFAULT_GUEST_USER_ID = "00000000-0000-0000-0000-000000000000"


class ConversationMemoryManager:
    """
    Gestor de memoria conversacional con persistencia en PostgreSQL.

    Usa AsyncSession para operaciones asíncronas.
    Incluye resumen automático para conversaciones largas.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.max_historial_llm = MAX_HISTORIAL_LLM
        self.resumen_umbral = RESUMEN_UMBRAL_MENSAJES

    def _validar_uuid(self, valor: str, campo: str) -> uuid.UUID:
        """Valida y convierte string a UUID."""
        try:
            return uuid.UUID(valor)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"{campo} debe ser un UUID válido: {valor}") from e

    async def _get_conversacion_db(self, conversacion_id: str, usuario_id: str) -> Optional[Conversacion]:
        """Obtiene conversación de BD verificando propiedad."""
        conv_uuid = self._validar_uuid(conversacion_id, "conversacion_id")
        user_uuid = self._validar_uuid(usuario_id, "usuario_id")
        stmt = select(Conversacion).where(
            Conversacion.id == conv_uuid,
            Conversacion.usuario_id == user_uuid
        ).options(selectinload(Conversacion.mensajes))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_conversacion_db_for_update(self, conversacion_id: str, usuario_id: str) -> Optional[Conversacion]:
        """Obtiene conversación con bloqueo FOR UPDATE para evitar condiciones de carrera."""
        conv_uuid = self._validar_uuid(conversacion_id, "conversacion_id")
        user_uuid = self._validar_uuid(usuario_id, "usuario_id")
        stmt = select(Conversacion).where(
            Conversacion.id == conv_uuid,
            Conversacion.usuario_id == user_uuid
        ).options(selectinload(Conversacion.mensajes)).with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _crear_conversacion_db(self, usuario_id: str, conversacion_id: Optional[str] = None) -> Conversacion:
        """Crea nueva conversación en BD."""
        user_uuid = self._validar_uuid(usuario_id, "usuario_id")
        cid = self._validar_uuid(conversacion_id, "conversacion_id") if conversacion_id else uuid.uuid4()
        conversacion = Conversacion(
            id=cid,
            usuario_id=user_uuid,
            productos_recientes=[],
            lista_mercado=[],
        )
        self.db.add(conversacion)
        await self.db.flush()
        return conversacion

    def _mapear_rol(self, rol: RolMensaje) -> TipoRemitente:
        """Mapea RolMensaje a TipoRemitente de BD."""
        mapping = {
            RolMensaje.USUARIO: TipoRemitente.USUARIO,
            RolMensaje.ASISTENTE: TipoRemitente.ASISTENTE,
            RolMensaje.SISTEMA: TipoRemitente.SISTEMA,
        }
        return mapping[rol]

    def _mapear_rol_inverso(self, rol: TipoRemitente) -> RolMensaje:
        """Mapea TipoRemitente de BD a RolMensaje."""
        mapping = {
            TipoRemitente.USUARIO: RolMensaje.USUARIO,
            TipoRemitente.ASISTENTE: RolMensaje.ASISTENTE,
            TipoRemitente.SISTEMA: RolMensaje.SISTEMA,
        }
        return mapping[rol]

    def _cargar_contexto_desde_bd(self, conv: Conversacion) -> ContextoConversacion:
        """Convierte modelo BD a ContextoConversacion en memoria sin forzar lazy load."""
        mensajes_list = []
        if "mensajes" in conv.__dict__ and conv.mensajes is not None:
            mensajes_list = [
                MensajeConversacion(
                    rol=self._mapear_rol_inverso(m.remitente),
                    contenido=m.contenido,
                    timestamp=m.creado_en,
                )
                for m in conv.mensajes
            ]

        ctx = ContextoConversacion(
            conversacion_id=str(conv.id),
            usuario_id=str(conv.usuario_id),
            mensajes=mensajes_list,
            productos_recientes=conv.productos_recientes or [],
            receta_actual=conv.receta_actual,
            lista_mercado_actual=conv.lista_mercado or [],
            presupuesto_actual=conv.presupuesto,
            resumen=conv.resumen,
            creada_en=conv.creado_en,
            actualizada_en=conv.actualizado_en,
            mensaje_count=len(mensajes_list),
        )
        return ctx


    async def _guardar_contexto_en_bd(self, ctx: ContextoConversacion) -> None:
        """Sincroniza contexto en memoria con BD usando bloqueo optimista."""
        # Usar FOR UPDATE para evitar condiciones de carrera
        conv = await self._get_conversacion_db_for_update(ctx.conversacion_id, ctx.usuario_id or "")
        if not conv:
            raise ValueError(f"Conversación {ctx.conversacion_id} no encontrada o no pertenece al usuario")

        conv.productos_recientes = ctx.productos_recientes
        conv.receta_actual = ctx.receta_actual
        conv.lista_mercado = ctx.lista_mercado_actual
        # Serializar presupuesto si es un dataclass o objeto complejo
        if ctx.presupuesto_actual is not None:
            if hasattr(ctx.presupuesto_actual, 'to_dict'):
                conv.presupuesto = ctx.presupuesto_actual.to_dict()
            elif hasattr(ctx.presupuesto_actual, '__dict__'):
                # Convertir recursivamente Decimal a float
                def _serializar_val(v):
                    from decimal import Decimal
                    if isinstance(v, Decimal):
                        return float(v)
                    elif hasattr(v, '__dict__'):
                        return {k: _serializar_val(val) for k, val in v.__dict__.items() if not k.startswith('_')}
                    elif isinstance(v, list):
                        return [_serializar_val(x) for x in v]
                    elif isinstance(v, dict):
                        return {k: _serializar_val(val) for k, val in v.items()}
                    return v
                conv.presupuesto = _serializar_val(ctx.presupuesto_actual)
            else:
                conv.presupuesto = ctx.presupuesto_actual
        else:
            conv.presupuesto = None
        conv.resumen = ctx.resumen
        conv.actualizado_en = datetime.now(timezone.utc)

        # Obtener el número real de mensajes en BD para evitar duplicados
        count_stmt = select(func.count(Mensaje.id)).where(Mensaje.conversacion_id == uuid.UUID(ctx.conversacion_id))
        count_result = await self.db.execute(count_stmt)
        mensajes_existentes = count_result.scalar() or 0

        # Solo guardar mensajes nuevos
        mensajes_nuevos = ctx.mensajes[mensajes_existentes:]

        for msg in mensajes_nuevos:
            mensaje_db = Mensaje(
                conversacion_id=uuid.UUID(ctx.conversacion_id),
                remitente=self._mapear_rol(msg.rol),
                contenido=msg.contenido,
                tokens_entrada=None,
                tokens_salida=None,
                modelo_usado=None,
            )
            self.db.add(mensaje_db)

        await self.db.flush()

    async def _generar_resumen_si_necesario(self, ctx: ContextoConversacion) -> None:
        """
        Genera resumen automático si la conversación supera el umbral.
        Usa el proveedor LLM configurado (Anthropic/Ollama) con fallback determinista.
        """
        if ctx.mensaje_count < self.resumen_umbral:
            return

        if ctx.resumen:
            # Ya tiene resumen generado
            return

        # Intentar resumen inteligente con LLM
        try:
            from app.services.llm import generar_texto
            prompt_resumen = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente que sintetiza de forma concisa (máximo 3 oraciones) "
                        "el contexto de compra y preferencias de un cliente de supermercado. "
                        "Destaca: recetas discutidas, productos preferidos o mencionados, presupuesto y necesidades dietéticas."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Resume el siguiente historial de conversación:\n" +
                        "\n".join([f"- {m.rol.value}: {m.contenido}" for m in ctx.mensajes[-15:]])
                    )
                }
            ]
            resumen_llm = await generar_texto(prompt_resumen)
            if resumen_llm:
                ctx.resumen = resumen_llm.strip()
                return
        except Exception as e:
            logger.warning(f"No fue posible generar resumen con LLM: {e}")

        # Fallback determinista estructurado
        temas = []
        if ctx.receta_actual:
            temas.append(f"receta: {ctx.receta_actual}")
        if ctx.productos_recientes:
            temas.append(f"productos: {', '.join(ctx.productos_recientes[:5])}")
        if ctx.lista_mercado_actual:
            items = [f"{i.get('cantidad', 1)}x {i.get('producto', 'item')}" for i in ctx.lista_mercado_actual[:3]]
            temas.append(f"lista mercado: {', '.join(items)}")

        ctx.resumen = f"Conversación de {ctx.mensaje_count} mensajes. Temas: {'; '.join(temas) if temas else 'general'}."

    # ===== API PÚBLICA =====

    async def obtener_o_crear(self, conversacion_id: Optional[str] = None, usuario_id: Optional[str] = None) -> ContextoConversacion:
        """
        Obtiene conversación existente o crea nueva.

        Si no se proporciona usuario_id, se asocia al usuario invitado por defecto.
        Si se proporciona conversacion_id, debe pertenecer al usuario.
        """
        uid = usuario_id or DEFAULT_GUEST_USER_ID

        if conversacion_id:
            # Buscar conversación existente del usuario
            conv = await self._get_conversacion_db(conversacion_id, uid)
            if conv:
                return self._cargar_contexto_desde_bd(conv)
            # Si se especificó un ID nuevo o no existe para este usuario, crearla si es un UUID válido
            try:
                self._validar_uuid(conversacion_id, "conversacion_id")
                conv = await self._crear_conversacion_db(uid, conversacion_id)
                await self.db.flush()
                return self._cargar_contexto_desde_bd(conv)
            except Exception:
                raise ValueError(f"Conversación {conversacion_id} no encontrada o no autorizada")

        # Crear nueva conversación
        conv = await self._crear_conversacion_db(uid, conversacion_id)
        await self.db.flush()
        return self._cargar_contexto_desde_bd(conv)

    async def guardar(self, contexto: ContextoConversacion) -> None:
        """
        Guarda/actualiza conversación en BD.

        Incluye generación de resumen automático si corresponde.
        """
        if not contexto.usuario_id:
            contexto.usuario_id = DEFAULT_GUEST_USER_ID

        await self._generar_resumen_si_necesario(contexto)
        await self._guardar_contexto_en_bd(contexto)
        await self.db.commit()

    async def agregar_mensaje(
        self,
        conversacion_id: str,
        usuario_id: str,
        rol: RolMensaje,
        contenido: str,
        productos_mencionados: Optional[List[str]] = None,
        receta_id: Optional[str] = None,
        intencion: Optional[str] = None,
        acciones_sugeridas: Optional[List[Dict[str, Any]]] = None,
    ) -> ContextoConversacion:
        """
        Agrega un mensaje a la conversación y actualiza contexto.

        Método conveniente que obtiene, actualiza y guarda en una operación.
        """
        ctx = await self.obtener_o_crear(conversacion_id, usuario_id)

        mensaje = MensajeConversacion(
            rol=rol,
            contenido=contenido,
            productos_mencionados=productos_mencionados or [],
            receta_id=receta_id,
            intencion=intencion,
            acciones_sugeridas=acciones_sugeridas or [],
        )
        ctx.agregar_mensaje(mensaje)

        await self.guardar(ctx)
        return ctx

    async def eliminar(self, conversacion_id: str, usuario_id: Optional[str] = None) -> bool:
        """
        Elimina una conversación (derecho al olvido - Ley 1581).

        Solo el propietario puede eliminar su conversación.
        Si usuario_id es None, se asume el usuario invitado.
        """
        self._validar_uuid(conversacion_id, "conversacion_id")
        uid = usuario_id or DEFAULT_GUEST_USER_ID
        self._validar_uuid(uid, "usuario_id")
        result = await self.db.execute(
            delete(Conversacion).where(
                Conversacion.id == uuid.UUID(conversacion_id),
                Conversacion.usuario_id == uuid.UUID(uid)
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def obtener_todas_usuario(self, usuario_id: Optional[str] = None, limite: int = 50) -> List[ContextoConversacion]:
        """
        Obtiene todas las conversaciones de un usuario (para exportación Ley 1581).

        Ordenadas por más reciente primero.
        """
        uid = usuario_id or DEFAULT_GUEST_USER_ID
        self._validar_uuid(uid, "usuario_id")
        stmt = select(Conversacion).where(
            Conversacion.usuario_id == uuid.UUID(uid)
        ).options(selectinload(Conversacion.mensajes)).order_by(Conversacion.actualizado_en.desc()).limit(limite)

        result = await self.db.execute(stmt)
        conversaciones = result.scalars().all()

        return [self._cargar_contexto_desde_bd(c) for c in conversaciones]

    async def limpiar_usuario(self, usuario_id: Optional[str] = None) -> int:
        """
        Elimina todas las conversaciones de un usuario (supresión Ley 1581).

        Retorna número de conversaciones eliminadas.
        """
        uid = usuario_id or DEFAULT_GUEST_USER_ID
        self._validar_uuid(uid, "usuario_id")
        result = await self.db.execute(
            delete(Conversacion).where(Conversacion.usuario_id == uuid.UUID(uid))
        )
        await self.db.commit()
        return result.rowcount

    async def obtener_historial_para_llm(self, conversacion_id: str, usuario_id: Optional[str] = None, limite: int = None) -> List[Dict[str, str]]:
        """
        Obtiene historial formateado para LLM directamente de BD.

        Verifica propiedad de la conversación antes de retornar historial.
        """
        self._validar_uuid(conversacion_id, "conversacion_id")
        uid = usuario_id or DEFAULT_GUEST_USER_ID
        self._validar_uuid(uid, "usuario_id")
        limite = limite or self.max_historial_llm

        # Verificar que la conversación pertenece al usuario
        conv = await self._get_conversacion_db(conversacion_id, uid)
        if not conv:
            raise ValueError(f"Conversación {conversacion_id} no encontrada o no autorizada")

        stmt = select(Mensaje).where(
            Mensaje.conversacion_id == uuid.UUID(conversacion_id)
        ).order_by(Mensaje.creado_en.desc()).limit(limite)

        result = await self.db.execute(stmt)
        mensajes = result.scalars().all()

        # Invertir para orden cronológico
        mensajes = list(reversed(mensajes))

        return [
            {"role": self._mapear_rol_inverso(m.remitente).value, "content": m.contenido}
            for m in mensajes
        ]

    async def obtener_contexto_resumido(self, conversacion_id: str, usuario_id: Optional[str] = None) -> str:
        """Obtiene resumen del contexto para inyectar en prompt."""
        self._validar_uuid(conversacion_id, "conversacion_id")
        uid = usuario_id or DEFAULT_GUEST_USER_ID
        self._validar_uuid(uid, "usuario_id")

        conv = await self._get_conversacion_db(conversacion_id, uid)
        if not conv:
            raise ValueError(f"Conversación {conversacion_id} no encontrada o no autorizada")

        ctx = self._cargar_contexto_desde_bd(conv)
        partes = [ctx.obtener_contexto_resumido()]
        if ctx.resumen:
            partes.append(f"Resumen previo: {ctx.resumen}")
        return " | ".join(partes)



from app.core.database import get_db

# Dependency injection para FastAPI
async def get_conversation_memory(db: AsyncSession = Depends(get_db)) -> ConversationMemoryManager:
    """Dependency injection para FastAPI."""
    return ConversationMemoryManager(db)
