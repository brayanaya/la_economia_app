from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Reemplaza 'app.db' o 'app.database' con la ruta real descubierta en el Paso 1
# Ejemplo: from app.core.database import get_db
from app.core.database import get_db

from app.schemas.agente import ChatAgenteRequest, ChatAgenteResponse
from app.services.agente import generar_respuesta_agente
from app.services.busqueda import buscar_productos_similares

router = APIRouter()


@router.post("/chat", response_model=ChatAgenteResponse)
async def agente_chat(
    payload: ChatAgenteRequest,
    db: AsyncSession = Depends(get_db),
):
    resultados = await buscar_productos_similares(
        db=db,
        consulta=payload.mensaje,
        limite=5,
        umbral_similitud=None,
    )

    resultados_relevantes = [
        prod for prod in resultados if prod.similitud >= 0.4
    ]

    respuesta_texto = await generar_respuesta_agente(payload.mensaje, resultados_relevantes)

    return ChatAgenteResponse(
        respuesta=respuesta_texto,
        productos_recomendados=resultados_relevantes,
        hubo_resultados_relevantes=len(resultados_relevantes) > 0,
    )
