import logging
import re

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.agente import AgenteChatRequest, AgenteChatResponse
from app.services.embeddings import get_embedding
from app.services.agente import generar_respuesta_agente, normalizar_texto
from app.api.v1.endpoints.busqueda import _buscar_candidatos, _aplicar_filtro_hibrido

logger = logging.getLogger("app.agente")

router = APIRouter()

# ---------------------------------------------------------------------------
# Clasificacion de intenciones: saludar, despedirse y las preguntas frecuentes
# se responden sin gastar consultas al retriever semantico.
# ---------------------------------------------------------------------------
_SOLO_SALUDO = {
    "hola", "holas", "holaa", "holis", "hey", "epa", "quiubo", "buenas",
    "buenos", "dias", "tardes", "noches", "dia", "buen", "que", "mas", "tal",
    "como", "estas", "vas", "va", "pues", "alla", "eh", "oiga", "amigo",
}
_SOLO_DESPEDIDA = {
    "gracias", "muchas", "chao", "adios", "hasta", "luego", "nos", "vemos",
    "listo", "perfecto", "bendiciones", "bye",
}
_FAQ_RE = re.compile(
    r"\b(pagos?|pagar|nequi|pse|tarjeta|bre ?b|transferencia|sedes?|ubicacion|"
    r"direccion|horario|entregas?|domicilio|envio|telefonos?|contacto|abren|"
    r"cierran|atienden)\b"
)
_RECETA_RE = re.compile(
    r"\b(desayun\w*|pericos?|calentado|almuerz\w*|cena|comida|receta\w*|"
    r"preparar|cocinar\w*|antojo\w*|sancocho|sopa|dulce|saludable\w*|"
    r"recomiend\w*|sugerencia\w*|ideas?)\b"
)

# Ingredientes tipicos por preparacion: la consulta semantica sola no trae
# toda la canasta, asi que cada preparacion amplia la busqueda.
_PREPARACIONES = [
    (r"\bpericos?\b", ("huevos", "tomate", "cebolla larga", "sal")),
    (r"\bcalentado\b", ("frijol", "arroz", "papa", "arepa", "huevos")),
    (r"\bchocolate\b", ("chocolate", "queso", "pan", "arepa")),
    (r"\bcafes?\b", ("cafe", "leche", "panela", "pan")),
    (r"\bdesayun\w*", ("huevos", "arepa", "pan", "cafe", "leche", "chocolate", "avena", "queso")),
    (r"\balmuerz\w*|\bsopa\b|\bsancocho\b|\bcena\b|\bcomida\b",
     ("arroz", "pollo", "papa", "tomate", "cebolla larga", "platano")),
    (r"\bsaludable\w*|\bsano\b|\bdieta\b", ("avena", "yogur", "lentejas", "tomate")),
    (r"\bantojo\w*|\bdulce\b", ("chocolate", "arepa", "panela", "gaseosa")),
]

_MAX_CONSULTAS = 9


def _clasificar_intencion(texto_plano: str) -> str:
    tokens = texto_plano.split()
    if tokens and all(token in _SOLO_SALUDO for token in tokens):
        return "saludo"
    if tokens and all(token in _SOLO_DESPEDIDA for token in tokens):
        return "despedida"
    if _FAQ_RE.search(texto_plano):
        return "faq"
    if _RECETA_RE.search(texto_plano):
        return "receta"
    return "busqueda"


def _consultas_recuperacion(mensaje: str, intencion: str = "busqueda") -> list[tuple[str, int]]:
    consultas = [(mensaje, 8)]
    if intencion == "receta":
        texto = normalizar_texto(mensaje)
        vistas = {mensaje}
        for patron, ingredientes in _PREPARACIONES:
            if re.search(patron, texto):
                for ingrediente in ingredientes:
                    if ingrediente not in vistas:
                        consultas.append((ingrediente, 3))
                        vistas.add(ingrediente)
    return consultas[:_MAX_CONSULTAS]


async def _recuperar_productos(
    db: AsyncSession, mensaje: str, sede_id, intencion: str = "busqueda"
) -> list:
    """
    Retrieval best-effort: si el proveedor de embeddings o la base falla,
    el agente responde sin productos en lugar de romper el chat.
    """
    por_producto: dict = {}
    try:
        for consulta, cantidad in _consultas_recuperacion(mensaje, intencion):
            vector_consulta = await get_embedding(consulta)
            candidatos = await _buscar_candidatos(db, vector_consulta, k=cantidad)
            recuperados = await _aplicar_filtro_hibrido(db, candidatos, sede_id)
            for producto in recuperados:
                actual = por_producto.get(producto.producto_id)
                if actual is None or producto.similitud > actual.similitud:
                    por_producto[producto.producto_id] = producto
    except Exception as exc:  # noqa: BLE001 - degradacion controlada
        logger.warning("El retriever fallo para el agente: %s", exc)
        return []
    return list(por_producto.values())


@router.post(
    "/chat",
    response_model=AgenteChatResponse,
    summary="Agente conversacional RAG: retriever semantico + filtro hibrido + generacion LLM",
)
async def agente_chat(
    payload: AgenteChatRequest, db: AsyncSession = Depends(get_db)
) -> AgenteChatResponse:
    intencion = _clasificar_intencion(normalizar_texto(payload.mensaje))

    # Saludos, despedidas y FAQ no necesitan retrieval: se responden directo.
    if intencion in ("saludo", "despedida", "faq"):
        resultados_relevantes = []
    else:
        resultados = sorted(
            await _recuperar_productos(db, payload.mensaje, payload.sede_id, intencion),
            key=lambda producto: producto.similitud,
            reverse=True,
        )
        mejor = max((r.similitud for r in resultados), default=0.0)
        piso = settings.umbral_similitud_minima
        if settings.embedding_provider == "ollama" and settings.ollama_embedding_model.startswith("nomic-embed-text"):
            piso = min(piso, 0.35)
        # Las recetas traen canastas completas por ingrediente: la ventana se
        # amplia para no cortar ingredientes con menor similitud lexica.
        ventana = 0.20 if intencion == "receta" else 0.10
        umbral = max(piso, mejor - ventana)
        resultados_relevantes = [r for r in resultados if r.similitud >= umbral][:8]

    historial = [(item.rol, item.texto) for item in payload.historial]
    respuesta_texto, generado_por_llm = await generar_respuesta_agente(
        payload.mensaje, resultados_relevantes, historial, intencion
    )

    return AgenteChatResponse(
        mensaje=payload.mensaje,
        respuesta=respuesta_texto,
        productos_recomendados=resultados_relevantes,
        hubo_resultados_relevantes=len(resultados_relevantes) > 0,
        generado_por_llm=generado_por_llm,
    )
