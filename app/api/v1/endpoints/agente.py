from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.core.config import settings
from app.core.database import get_db
from app.schemas.agente import AgenteChatRequest, AgenteChatResponse
from app.services.embeddings import get_embedding
from app.services.agente import generar_respuesta_agente
from app.services.recetas import detectar_intencion_receta, obtener_receta_por_id
from app.api.v1.endpoints.busqueda import _buscar_candidatos, _aplicar_filtro_hibrido

router = APIRouter()


@router.post(
    "/chat",
    response_model=AgenteChatResponse,
    summary="Agente conversacional RAG: Aya - asistente experta de compras y cocina",
)
async def agente_chat(
    payload: AgenteChatRequest, db: AsyncSession = Depends(get_db)
) -> AgenteChatResponse:
    """
    Flujo completo de Aya:
    1. Detecta si el usuario pide una receta específica
    2. Busca productos relevantes por similitud semántica
    3. Aplica filtro híbrido por stock/sede
    4. Genera respuesta conversacional con el prompt maestro de Aya
    """
    # 1. Detectar intención de receta ANTES de buscar productos
    receta_id = detectar_intencion_receta(payload.mensaje)
    receta_detectada = receta_id if receta_id else None

    # 2. Búsqueda semántica de productos
    vector_consulta = await get_embedding(payload.mensaje)
    candidatos = await _buscar_candidatos(db, vector_consulta, k=8)
    resultados = await _aplicar_filtro_hibrido(db, candidatos, payload.sede_id)

    # Umbral dinámico: piso configurable + margen relativo al mejor resultado
    mejor = max((r.similitud for r in resultados), default=0.0)
    umbral = max(settings.umbral_similitud_minima, mejor - 0.10)
    resultados_relevantes = [r for r in resultados if r.similitud >= umbral][:4]

    # 3. Generar respuesta con Aya (incluye info de receta si se detectó)
    respuesta_texto = await generar_respuesta_agente(
        payload.mensaje,
        resultados_relevantes,
        receta_detectada=receta_detectada
    )

    # 4. Preparar datos de receta para el frontend (si aplica)
    receta_data = None
    if receta_detectada:
        receta = obtener_receta_por_id(receta_detectada)
        if receta:
            receta_data = {
                "id": receta.id,
                "nombre": receta.nombre,
                "descripcion": receta.descripcion,
                "categoria": receta.categoria,
                "tiempo_min": receta.tiempo_min,
                "porciones": receta.porciones,
                "costo_estimado_cop": receta.costo_estimado_cop,
                "imagen_url": receta.imagen_url,
                "ingredientes": [
                    {
                        "nombre": ing.nombre,
                        "cantidad": ing.cantidad,
                        "busqueda_catalogo": ing.busqueda_catalogo,
                        "obligatorio": ing.obligatorio,
                        "notas": ing.notas,
                    }
                    for ing in receta.ingredientes
                ],
                "pasos": receta.pasos,
                "tags": receta.tags,
            }

    return AgenteChatResponse(
        mensaje=payload.mensaje,
        respuesta=respuesta_texto,
        productos_recomendados=resultados_relevantes,
        hubo_resultados_relevantes=len(resultados_relevantes) > 0,
        receta=receta_data,
    )