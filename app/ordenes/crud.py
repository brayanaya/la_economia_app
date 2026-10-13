# carrito-v1
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Orden


async def obtener_orden(db: AsyncSession, orden_id: UUID) -> Optional[Orden]:
    """Busca una orden por su id (con sus items). Devuelve None si no existe."""
    resultado = await db.execute(
        select(Orden).options(selectinload(Orden.items)).where(Orden.id == orden_id)
    )
    return resultado.scalar_one_or_none()
