from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.agente import AgenteChatRequest, AgenteChatResponse
from app.services.embeddings import get_embedding
from app.services.agente import generar_respuesta_agente
from app.api.v1.endpoints.busqueda import _buscar_candidatos, _aplicar_filtro_hibrido

router = APIRouter()


@router.post(
    "/chat",
    response_model=AgenteChatResponse,
    summary="Agente conversacional RAG: retriever semantico + filtro hibrido + generacion LLM",
)
async def agente_chat(
    payload: AgenteChatRequest, db: AsyncSession = Depends(get_db)
) -> AgenteChatResponse:
    vector_consulta = await get_embedding(payload.mensaje)

    candidatos = await _buscar_candidatos(db, vector_consulta, k=8)
    resultados = await _aplicar_filtro_hibrido(db, candidatos, payload.sede_id)

    resultados_relevantes = [
        r for r in resultados if r.similitud >= settings.umbral_similitud_minima
    ]

    respuesta_texto = await generar_respuesta_agente(payload.mensaje, resultados_relevantes)

    return AgenteChatResponse(
        mensaje=payload.mensaje,
        respuesta=respuesta_texto,
        productos_recomendados=resultados_relevantes,
        hubo_resultados_relevantes=len(resultados_relevantes) > 0,
    )
