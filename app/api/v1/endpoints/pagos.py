import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.ordenes.models import Orden


router = APIRouter()


class PagoRequest(BaseModel):
    orden_id: UUID


@router.post("/procesar")
async def procesar_pago(
    payload: PagoRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Simula el pago de una orden pendiente."""
    resultado = await db.execute(
        select(Orden)
        .where(Orden.id == payload.orden_id)
        .with_for_update()
    )
    orden = resultado.scalar_one_or_none()

    if orden is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado",
        )

    if orden.estado.lower() == "pagado":
        return {
            "orden_id": str(orden.id),
            "estado": "PAGADO",
            "ticket_id": str(orden.ticket_id),
            "total": str(orden.total),
        }

    if orden.estado.lower() != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El pedido no está pendiente de pago",
        )

    await asyncio.sleep(1)
    orden.estado = "PAGADO"
    await db.commit()

    return {
        "orden_id": str(orden.id),
        "estado": "PAGADO",
        "ticket_id": str(orden.ticket_id),
        "total": str(orden.total),
    }

