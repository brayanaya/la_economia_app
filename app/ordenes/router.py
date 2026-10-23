# carrito-v1
import uuid
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db as get_db
from app.auth.router import current_session, check_csrf
from app.auth.models import CustomerSession
from .crud import obtener_orden
from .models import DetalleOrden, Orden
from .schemas import OrdenConsultaOut, OrdenCreate, OrdenOut

router = APIRouter(prefix="/ordenes", tags=["ordenes"])
CENTAVOS = Decimal("0.01")


@router.post("/", response_model=OrdenOut, status_code=status.HTTP_201_CREATED)
async def crear_orden(payload: OrdenCreate, request: Request, session: CustomerSession = Depends(current_session), db: AsyncSession = Depends(get_db)):
    check_csrf(request, session)
    orden_id = uuid.uuid4()
    total = Decimal("0")
    detalles = []
    for it in payload.items:
        subtotal = (it.precio_unitario * it.cantidad).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
        total += subtotal
        detalles.append(
            DetalleOrden(
                id=uuid.uuid4(),
                orden_id=orden_id,
                producto_id=it.producto_id,
                nombre=it.nombre,
                imagen_url=it.imagen_url,
                cantidad=it.cantidad,
                precio_unitario=it.precio_unitario,
                subtotal=subtotal,
            )
        )

    orden = Orden(
        id=orden_id,
        sede_id=payload.sede_id,
        customer_id=session.user_id,
        cliente_nombre=payload.cliente_nombre,
        cliente_telefono=payload.cliente_telefono,
        notas=payload.notas,
        total=total,
        estado="pendiente",
        items=detalles,
    )
    db.add(orden)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Sede invalida o datos inconsistentes")

    resultado = await db.execute(
        select(Orden)
        .options(selectinload(Orden.items))
        .where(Orden.id == orden_id)
        .execution_options(populate_existing=True)
    )
    return resultado.scalar_one()


@router.get("/{orden_id}", response_model=OrdenConsultaOut)
async def consultar_orden(orden_id: uuid.UUID, response: Response, db: AsyncSession = Depends(get_db)):
    orden = await obtener_orden(db, orden_id)
    if orden is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    response.headers["Cache-Control"] = "no-store"
    return orden
