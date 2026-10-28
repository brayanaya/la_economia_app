# carrito-v1
import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import CustomerSession
from app.auth.router import check_csrf, current_session
from app.core.config import settings
from app.core.database import get_db as get_db
from app.ordenes.crud import obtener_orden
from app.ordenes.models import Orden
from .models import Pago
from .schemas import (
    ConfiguracionPagoOut,
    EstadoPagoOut,
    InicioPagoOut,
    IniciarPagoIn,
    PagoOut,
    WebhookResultadoOut,
)
from .wompi import ESTADOS_WOMPI, construir_firma_integridad, consultar_transaccion, monto_centavos, verificar_checksum_evento

logger = logging.getLogger("app.pagos")

router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.post(
    "/ordenes/{orden_id}/iniciar",
    response_model=InicioPagoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Inicia el pago en linea (Wompi) de una orden propia y devuelve el formulario de redireccion",
)
async def iniciar_pago(
    orden_id,
    payload: IniciarPagoIn,
    request: Request,
    session: CustomerSession = Depends(current_session),
    db: AsyncSession = Depends(get_db),
) -> InicioPagoOut:
    check_csrf(request, session)
    if not settings.wompi_configurada:
        raise HTTPException(
            status_code=503,
            detail="La pasarela de pago en linea no esta configurada en este entorno. Puedes finalizar tu pedido con pago contra entrega.",
        )

    orden = await obtener_orden(db, orden_id)
    if orden is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if orden.customer_id != session.user_id:
        raise HTTPException(status_code=403, detail="Este pedido no pertenece a tu cuenta")
    if orden.estado == "pagado":
        raise HTTPException(status_code=409, detail="Este pedido ya esta pagado")

    monto = monto_centavos(orden.total)
    referencia = f"LEA-{orden.id.hex[:12].upper()}-{secrets.token_hex(2).upper()}"
    pago = Pago(
        orden_id=orden.id,
        proveedor="wompi",
        estado="pendiente",
        referencia=referencia,
        monto_centavos=monto,
        moneda="COP",
    )
    db.add(pago)
    await db.commit()
    await db.refresh(pago)

    # Campos del formulario oculto para el Web Checkout de Wompi.
    # "integrity-sing" es el nombre oficial que documenta Wompi (con esa
    # errata) para la firma de integridad.
    campos = {
        "public-key": settings.wompi_public_key,
        "currency": "COP",
        "amount-in-cents": str(monto),
        "reference": referencia,
        "integrity-sing": construir_firma_integridad(
            monto, "COP", referencia, settings.wompi_integrity_secret
        ),
        "redirect-url": f"{settings.app_public_url.rstrip('/')}/pedidos/{orden.id}",
    }

    return InicioPagoOut(pago=PagoOut.model_validate(pago), accion=settings.wompi_checkout_url, campos=campos)


@router.get(
    "/configuracion",
    response_model=ConfiguracionPagoOut,
    summary="Medios de pago disponibles en este entorno (vista publica)",
)
async def configuracion_pagos(response: Response) -> ConfiguracionPagoOut:
    response.headers["Cache-Control"] = "no-store"
    return ConfiguracionPagoOut(pasarela_configurada=settings.wompi_configurada)


@router.get(
    "/ordenes/{orden_id}",
    response_model=EstadoPagoOut,
    summary="Estado de pago de una orden (vista publica del ticket)",
)
async def estado_pago(orden_id, response: Response, db: AsyncSession = Depends(get_db)) -> EstadoPagoOut:
    orden = await obtener_orden(db, orden_id)
    if orden is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    resultado = await db.execute(
        select(Pago)
        .where(Pago.orden_id == orden.id)
        .order_by(Pago.creado_en.desc(), Pago.id.desc())
        .limit(1)
    )
    pago = resultado.scalar_one_or_none()

    response.headers["Cache-Control"] = "no-store"
    return EstadoPagoOut(
        orden_id=orden.id,
        orden_estado=orden.estado,
        metodo=orden.metodo_pago,
        pasarela_configurada=settings.wompi_configurada,
        pago=PagoOut.model_validate(pago) if pago else None,
    )


@router.post(
    "/webhook/wompi",
    response_model=WebhookResultadoOut,
    summary="Webhook server-to-server de eventos de transaccion de Wompi",
)
async def webhook_wompi(request: Request, db: AsyncSession = Depends(get_db)) -> WebhookResultadoOut:
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001 - cuerpo no JSON
        raise HTTPException(status_code=400, detail="Evento invalido")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Evento invalido")

    # 1. Autenticidad del evento con el secreto de eventos, si esta configurado.
    firma_verificada = False
    if settings.wompi_events_secret:
        if not verificar_checksum_evento(payload, settings.wompi_events_secret):
            logger.warning("Evento de Wompi rechazado: checksum invalido")
            raise HTTPException(status_code=401, detail="Checksum de evento invalido")
        firma_verificada = True

    transaccion = (payload.get("data") or {}).get("transaction")
    if not isinstance(transaccion, dict) or "id" not in transaccion or "reference" not in transaccion:
        return WebhookResultadoOut(ok=True, detalle="Evento sin transaccion; ignorado")

    estado_wompi = str(transaccion.get("status", "")).upper()
    estado = ESTADOS_WOMPI.get(estado_wompi)
    if estado is None:
        return WebhookResultadoOut(ok=True, detalle=f"Estado {estado_wompi} no relevante; ignorado")

    resultado = await db.execute(select(Pago).where(Pago.referencia == transaccion["reference"]))
    pago = resultado.scalar_one_or_none()
    if pago is None:
        # Referencia desconocida: se responde 200 para que Wompi no reintente.
        return WebhookResultadoOut(ok=True, detalle="Referencia desconocida; ignorado")

    pago.estado = estado
    pago.transaccion_id = str(transaccion["id"])
    pago.metadatos = payload

    # 2. La aprobacion exige monto exacto y, ademas, verificacion contra la
    #    API de Wompi o firma de eventos valida (ver docstring de wompi.py).
    if estado == "aprobado":
        aprobado = False
        monto_evento = transaccion.get("amount_in_cents")
        if monto_evento != pago.monto_centavos:
            logger.warning(
                "Evento APPROVED con monto %s != %s para la referencia %s; no se aprueba",
                monto_evento, pago.monto_centavos, pago.referencia,
            )
        elif settings.wompi_public_key:
            try:
                verificacion = await consultar_transaccion(str(transaccion["id"]))
            except Exception as exc:  # noqa: BLE001 - falla de red al verificar
                logger.warning("No se pudo verificar con la API de Wompi: %s", exc)
                verificacion = None
            if verificacion and verificacion.get("status") == "APPROVED":
                aprobado = (
                    verificacion.get("amount_in_cents") == pago.monto_centavos
                    and verificacion.get("reference") == pago.referencia
                )
            elif verificacion is None and firma_verificada:
                # API inalcanzable pero la firma del evento es criptograficamente
                # valida: el evento provino de Wompi y el monto ya coincide.
                aprobado = True
            elif verificacion is not None:
                logger.warning(
                    "La API de Wompi no confirma la transaccion %s; no se aprueba",
                    transaccion["id"],
                )
        elif firma_verificada:
            # Sin public key no se puede verificar contra la API; la firma de
            # eventos valida + monto exacto son la evidencia.
            aprobado = True
        else:
            logger.warning(
                "Evento APPROVED sin poder verificar (sin firma ni public key); el pago queda pendiente"
            )

        if aprobado:
            pago.estado = "aprobado"
            orden = await db.get(Orden, pago.orden_id)
            if orden is not None:
                orden.estado = "pagado"
        else:
            pago.estado = "pendiente"

    elif estado == "anulado":
        # Un cobro aprobado que Wompi anula despues: el pedido vuelve a
        # estar pendiente de pago.
        orden = await db.get(Orden, pago.orden_id)
        if orden is not None and orden.estado == "pagado":
            orden.estado = "pendiente"

    await db.commit()
    return WebhookResultadoOut(ok=True, detalle=f"Pago {pago.referencia}: {pago.estado}")
