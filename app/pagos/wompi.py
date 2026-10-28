# carrito-v1
"""
Servicio de integracion con Wompi (pasarela de pagos de Colombia:
tarjeta, PSE, Nequi, Bancolombia, etc.).

Flujo soportado — Web Checkout:
1. El backend crea un registro `Pago` con una referencia unica y calcula
   la firma de integridad: SHA-256 de "{monto_centavos}{moneda}{referencia}{secreto}".
   El secreto nunca llega al navegador.
2. El frontend hace POST (formulario oculto) a `wompi_checkout_url` con los
   campos que devuelve el endpoint de inicio de pago; Wompi muestra su
   pagina de cobro y redirige de vuelta al ticket del pedido.
3. Wompi notifica el resultado al webhook server-to-server. La aprobacion
   del pedido NUNCA depende solo del webhook: se exige (a) firma de eventos
   valida (WOMPI_EVENTS_SECRET) y/o (b) verificacion server-to-server con
   la API publica de transacciones de Wompi (status, monto y referencia
   deben coincidir exactamente con lo registrado en el `Pago`).

Con esto, un webhook falsificado no puede marcar un pedido como pagado.
"""
import hashlib
import hmac
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

import httpx

from app.core.config import settings

# Mapeo de estados de transaccion de Wompi -> estado interno del pago.
ESTADOS_WOMPI = {
    "APPROVED": "aprobado",
    "DECLINED": "declinado",
    "VOIDED": "anulado",
    "ERROR": "error",
    "PENDING": "pendiente",
}


def monto_centavos(total: Decimal) -> int:
    """Convierte el total Decimal de la orden a centavos (entero Wompi)."""
    return int((total * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def construir_firma_integridad(
    monto_centavos: int, moneda: str, referencia: str, secreto: str
) -> str:
    """
    Firma de integridad del Web Checkout:
    SHA-256 de "{amount-in-cents}{currency}{reference}{integrity_secret}".
    """
    carga = f"{monto_centavos}{moneda}{referencia}{secreto}"
    return hashlib.sha256(carga.encode()).hexdigest()


def _valor_propiedad(payload: dict, propiedad: str) -> str:
    """Recorre rutas tipo "transaction.id" dentro del evento de Wompi."""
    actual: Any = payload
    for parte in propiedad.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return ""
        actual = actual[parte]
    if actual is None:
        return ""
    return str(actual)


def calcular_checksum_evento(payload: dict, propiedades: list[str], secreto: str) -> str:
    """
    Checksum de un evento de Wompi: SHA-256 de la concatenacion de los
    valores de las propiedades firmadas (en el orden listado) + secreto.
    """
    carga = "".join(_valor_propiedad(payload, propiedad) for propiedad in propiedades)
    return hashlib.sha256((carga + secreto).encode()).hexdigest()


def verificar_checksum_evento(payload: dict, secreto: str) -> bool:
    """
    Valida `signature.checksum` del evento con el secreto de eventos.
    Devuelve False si el evento no trae firma o el secreto esta vacio.
    """
    firma = payload.get("signature")
    if not isinstance(firma, dict) or not secreto:
        return False
    checksum = firma.get("checksum")
    propiedades = firma.get("properties")
    if not isinstance(checksum, str) or not isinstance(propiedades, list):
        return False
    esperado = calcular_checksum_evento(payload, propiedades, secreto)
    return hmac.compare_digest(esperado, checksum)


async def consultar_transaccion(transaccion_id: str) -> Optional[dict]:
    """
    Consulta la transaccion en la API publica de Wompi (server-to-server).
    Devuelve el objeto `transaction` o None si no existe/falla la consulta.
    Las excepciones de red se propagan para que el llamador distinga
    "no pude verificar" de "verifique y no coincide".
    """
    url = (
        f"{settings.wompi_api_base_resuelta}/transactions/{transaccion_id}"
        f"?public_key={settings.wompi_public_key}"
    )
    async with httpx.AsyncClient(timeout=15.0) as cliente:
        respuesta = await cliente.get(url)
        respuesta.raise_for_status()
        datos = respuesta.json().get("data") or {}
    transaccion = datos.get("transaction")
    return transaccion if isinstance(transaccion, dict) else None
