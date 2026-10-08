from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.consentimiento import ConsentimientoHabeasData
from app.schemas.legal import ConsentimientoCreate, ConsentimientoResponse

router = APIRouter()


@router.post(
    "/consentimiento",
    response_model=ConsentimientoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra la autorizacion de tratamiento de datos y cookies (Ley 1581)",
)
async def registrar_consentimiento(
    payload: ConsentimientoCreate, request: Request, db: AsyncSession = Depends(get_db)
) -> ConsentimientoResponse:
    # Solo la IP del socket: X-Forwarded-For lo controla el cliente y falsificaria la auditoria.
    ip = request.client.host if request.client else "desconocida"
    registro = ConsentimientoHabeasData(
        ip_origen=ip[:45],
        user_agent=(request.headers.get("user-agent") or "")[:512] or None,
        acepto_politica=payload.acepto_politica,
        acepto_cookies=payload.acepto_cookies,
        version_politica=payload.version_politica,
    )
    db.add(registro)
    await db.commit()
    await db.refresh(registro)
    return ConsentimientoResponse.model_validate(registro)