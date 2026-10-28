# carrito-v1
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IniciarPagoIn(BaseModel):
    """Solicitud para iniciar un cobro en linea de una orden propia."""

    model_config = ConfigDict(str_strip_whitespace=True)

    metodo: Literal["wompi"] = "wompi"


class PagoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estado: str
    referencia: str
    monto_centavos: int
    moneda: str
    transaccion_id: Optional[str] = None
    creado_en: datetime


class InicioPagoOut(BaseModel):
    """
    Datos para redirigir al cliente al checkout de Wompi:

    - accion: URL a la que se hace POST (form HTML).
    - campos: inputs ocultos del formulario; el backend ya calculo la firma
      de integridad con el secreto, que nunca sale del servidor.
    """

    pago: PagoOut
    accion: str
    campos: dict[str, str]


class ConfiguracionPagoOut(BaseModel):
    """Vista publica para que el frontend sepa que medios de pago ofrecer."""

    pasarela_configurada: bool


class EstadoPagoOut(BaseModel):
    """Vista publica del estado de pago de una orden (para el ticket)."""

    orden_id: UUID
    orden_estado: str
    metodo: Optional[str] = None
    pasarela_configurada: bool
    pago: Optional[PagoOut] = None


class WebhookResultadoOut(BaseModel):
    ok: bool
    detalle: str = Field(default="")
