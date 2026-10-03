from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.categoria import Categoria
from app.models.embedding import EmbeddingProducto
from app.models.inventario import InventarioSede
from app.models.producto import Producto
from app.schemas.busqueda import (
    BusquedaSemanticaRequest,
    BusquedaSemanticaResponse,
    ProductoRecuperado,
)
from app.services.embeddings import get_embedding

router = APIRouter(prefix="/busqueda", tags=["Búsqueda semántica (RAG)"])


async def _buscar_candidatos(
    db: AsyncSession, vector_consulta: list[float], k: int
) -> list[tuple[EmbeddingProducto, float]]:
    """
    Ejecuta la búsqueda por similitud coseno usando el operador `<=>` de
    pgvector sobre el índice HNSW de embeddings_productos (numeral 10.3).
    """
    distancia = EmbeddingProducto.embedding.cosine_distance(vector_consulta)
    stmt = (
        select(EmbeddingProducto, distancia.label("distancia"))
        .order_by(distancia)
        .limit(k)
    )
    filas = (await db.execute(stmt)).all()
    # similitud coseno = 1 - distancia coseno
    return [(fila.EmbeddingProducto, 1 - fila.distancia) for fila in filas]


@router.post(
    "/semantica",
    response_model=BusquedaSemanticaResponse,
    summary="Retriever RAG: búsqueda semántica + filtro híbrido por stock/sede",
)
async def busqueda_semantica(
    payload: BusquedaSemanticaRequest, db: AsyncSession = Depends(get_db)
) -> BusquedaSemanticaResponse:
    """
    Implementa el flujo del retriever descrito en el numeral 10.3 del
    documento de arquitectura: (1) recuperación semántica amplia sobre el
    índice HNSW, (2) filtro híbrido de disponibilidad por sede activa, y
    (3) fallback ampliando k si el filtro deja menos de dos candidatos.
    """
    vector_consulta = await get_embedding(payload.consulta)

    candidatos = await _buscar_candidatos(db, vector_consulta, payload.top_k)
    candidatos_ampliados = False

    resultados = await _aplicar_filtro_hibrido(db, candidatos, payload.sede_id)

    # Fallback: si el filtro híbrido deja menos de 2 candidatos disponibles,
    # se amplía la búsqueda inicial a k=16 antes de responder al cliente.
    if payload.sede_id is not None and len(resultados) < 2 and payload.top_k < 16:
        candidatos_ampliados = True
        candidatos = await _buscar_candidatos(db, vector_consulta, 16)
        resultados = await _aplicar_filtro_hibrido(db, candidatos, payload.sede_id)

    resultados = resultados[: payload.limite_resultados]

    return BusquedaSemanticaResponse(
        consulta=payload.consulta,
        resultados=resultados,
        candidatos_ampliados=candidatos_ampliados,
    )


async def _aplicar_filtro_hibrido(
    db: AsyncSession,
    candidatos: list[tuple[EmbeddingProducto, float]],
    sede_id,
) -> list[ProductoRecuperado]:
    """
    Aplica el filtro estructurado (stock > 0 en la sede activa) sobre los
    candidatos semánticos, conservando el orden de similitud descendente.
    Si no se especifica sede_id, retorna los candidatos sin filtrar stock
    (útil para consultas generales de catálogo sin sede seleccionada).
    """
    resultados: list[ProductoRecuperado] = []

    for embedding_row, similitud in candidatos:
        producto = await db.get(
            Producto, embedding_row.producto_id, options=[]
        )
        if producto is None:
            continue

        categoria = await db.get(Categoria, producto.categoria_id)

        stock_sede = None
        if sede_id is not None:
            inv_stmt = select(InventarioSede).where(
                InventarioSede.producto_id == producto.id,
                InventarioSede.sede_id == sede_id,
            )
            inventario = (await db.execute(inv_stmt)).scalar_one_or_none()
            if inventario is None or inventario.stock_actual <= 0:
                continue  # descartado por el filtro híbrido de disponibilidad
            stock_sede = inventario.stock_actual

        resultados.append(
            ProductoRecuperado(
                producto_id=producto.id,
                nombre=producto.nombre,
                categoria_nombre=categoria.nombre if categoria else None,
                precio=producto.precio_venta,
                stock_sede=stock_sede,
                similitud=round(similitud, 4),
            )
        )

    return resultados
