import re
import unicodedata

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.agente import AgenteChatRequest, AgenteChatResponse
from app.services.embeddings import get_embedding
from app.services.agente import generar_respuesta_agente
from app.api.v1.endpoints.busqueda import _buscar_candidatos, _aplicar_filtro_hibrido

router = APIRouter()


def _consultas_recuperacion(mensaje: str) -> list[tuple[str, int]]:
    texto = "".join(
        caracter for caracter in unicodedata.normalize("NFD", mensaje.lower())
        if unicodedata.category(caracter) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9 ]", " ", texto)
    consultas = [(mensaje, 8)]
    if re.search(r"\bhuevos?\s+pericos?\b", texto):
        consultas.extend((ingrediente, 4) for ingrediente in ("huevos", "tomate", "cebolla larga", "sal"))
    return consultas


@router.post(
    "/chat",
    response_model=AgenteChatResponse,
    summary="Agente conversacional RAG: retriever semantico + filtro hibrido + generacion LLM",
)
async def agente_chat(
    payload: AgenteChatRequest, db: AsyncSession = Depends(get_db)
) -> AgenteChatResponse:
    por_producto = {}
    for consulta, cantidad in _consultas_recuperacion(payload.mensaje):
        vector_consulta = await get_embedding(consulta)
        candidatos = await _buscar_candidatos(db, vector_consulta, k=cantidad)
        recuperados = await _aplicar_filtro_hibrido(db, candidatos, payload.sede_id)
        for producto in recuperados:
            actual = por_producto.get(producto.producto_id)
            if actual is None or producto.similitud > actual.similitud:
                por_producto[producto.producto_id] = producto

    resultados = sorted(por_producto.values(), key=lambda producto: producto.similitud, reverse=True)
    mejor = max((r.similitud for r in resultados), default=0.0)
    piso = settings.umbral_similitud_minima
    if settings.embedding_provider == "ollama" and settings.ollama_embedding_model.startswith("nomic-embed-text"):
        piso = min(piso, 0.35)
    umbral = max(piso, mejor - 0.10)
    resultados_relevantes = [r for r in resultados if r.similitud >= umbral][:6]

    historial = [(item.rol, item.texto) for item in payload.historial]
    respuesta_texto = await generar_respuesta_agente(
        payload.mensaje, resultados_relevantes, historial
    )

    return AgenteChatResponse(
        mensaje=payload.mensaje,
        respuesta=respuesta_texto,
        productos_recomendados=resultados_relevantes,
        hubo_resultados_relevantes=len(resultados_relevantes) > 0,
    )
