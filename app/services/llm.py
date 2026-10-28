"""
Capa de proveedores de LLM para el agente conversacional.

Selecciona el proveedor con la variable LLM_PROVIDER:

- "ollama": modelo local servido por Ollama (/api/chat), gratuito.
- "anthropic": modelo de Claude mediante la API oficial de Anthropic
  (requiere ANTHROPIC_API_KEY; usa el SDK `anthropic` ya incluido en
  requirements.txt).
- "auto" (predeterminado): prueba Claude si hay API key configurada y,
  si no, Ollama. Si ninguno responde, `generar_texto` devuelve None y el
  agente construye una respuesta determinista con los productos
  recuperados, de modo que el chat nunca quede fuera de servicio.

Todos los proveedores exponen `generar(mensajes) -> str`, donde
`mensajes` usa el formato OpenAI/Ollama: [{"role": ..., "content": ...}]
con el system prompt como primer mensaje (rol "system").
"""
from __future__ import annotations

import logging
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger("app.llm")


class ProveedorLLM(Protocol):
    nombre: str

    async def generar(self, mensajes: list[dict]) -> str: ...


class ProveedorOllama:
    """Genera respuestas con un modelo local servido por Ollama (/api/chat)."""

    def __init__(self, base_url: str, modelo: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._modelo = modelo
        self.nombre = f"ollama:{modelo}"

    async def generar(self, mensajes: list[dict]) -> str:
        async with httpx.AsyncClient(timeout=60.0) as cliente:
            respuesta = await cliente.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._modelo,
                    "messages": mensajes,
                    "stream": False,
                    "options": {"temperature": 0.45},
                },
            )
            respuesta.raise_for_status()
            return respuesta.json()["message"]["content"]


class ProveedorAnthropic:
    """
    Genera respuestas con Claude mediante la API oficial de Anthropic.

    Notas de implementacion:
    - El SDK se importa de forma diferida para no acoplar el resto de la
      app a la dependencia cuando se usa otro proveedor.
    - No se envia temperature/top_p/top_k: la API actual de Anthropic los
      rechaza, y el system prompt ya fija el tono del asistente.
    - No se envia `thinking`: en los modelos actuales de Claude el modo
      adaptativo es el comportamiento por defecto.
    - Los bloques de razonamiento (thinking) que puedan venir en la
      respuesta se ignoran; solo se une el texto de los bloques tipo "text".
    """

    def __init__(self, api_key: str, modelo: str, max_tokens: int) -> None:
        from anthropic import AsyncAnthropic  # import diferido

        self._cliente = AsyncAnthropic(api_key=api_key)
        self._modelo = modelo
        self._max_tokens = max_tokens
        self.nombre = f"anthropic:{modelo}"

    async def generar(self, mensajes: list[dict]) -> str:
        system = None
        conversacion = mensajes
        if mensajes and mensajes[0].get("role") == "system":
            system = mensajes[0]["content"]
            conversacion = mensajes[1:]

        respuesta = await self._cliente.messages.create(
            model=self._modelo,
            max_tokens=self._max_tokens,
            system=system,
            messages=conversacion,
        )
        if getattr(respuesta, "stop_reason", None) == "refusal":
            raise RuntimeError("Claude rechazo la solicitud (stop_reason=refusal)")
        return "".join(
            bloque.text
            for bloque in respuesta.content
            if getattr(bloque, "type", None) == "text"
        )


def construir_proveedores() -> list[ProveedorLLM]:
    """
    Proveedores activos segun LLM_PROVIDER, en orden de preferencia.
    Lista vacia = solo respondedor determinista.
    """
    proveedores: list[ProveedorLLM] = []
    if settings.llm_provider in ("anthropic", "auto"):
        if not settings.anthropic_api_key:
            if settings.llm_provider == "anthropic":
                logger.error(
                    "LLM_PROVIDER=anthropic sin ANTHROPIC_API_KEY; se usara el respondedor determinista"
                )
        else:
            proveedores.append(
                ProveedorAnthropic(
                    api_key=settings.anthropic_api_key,
                    modelo=settings.anthropic_chat_model,
                    max_tokens=settings.llm_max_tokens,
                )
            )
    if settings.llm_provider in ("ollama", "auto"):
        proveedores.append(
            ProveedorOllama(base_url=settings.ollama_base_url, modelo=settings.llm_model)
        )
    return proveedores


async def generar_texto(mensajes: list[dict]) -> str | None:
    """
    Devuelve el texto del primer proveedor que responda, o None si no hay
    proveedores configurados o todos fallan (se registran los errores).
    Nunca lanza: el llamador decide como degradar.
    """
    for proveedor in construir_proveedores():
        try:
            texto = await proveedor.generar(mensajes)
        except Exception as exc:  # noqa: BLE001 - degradacion controlada
            logger.warning("Proveedor LLM %s fallo: %s", proveedor.nombre, exc)
            continue
        if texto and texto.strip():
            return texto.strip()
        logger.warning("Proveedor LLM %s devolvio una respuesta vacia", proveedor.nombre)
    return None
