import httpx

from app.core.config import settings
from app.schemas.busqueda import ProductoRecuperado


def _construir_contexto(productos: list[ProductoRecuperado]) -> str:
    if not productos:
        return "No se encontraron productos relevantes en el catalogo para esta consulta. No conoces el inventario actual: NO menciones ningun producto, categoria ni marca concretos."

    lineas = []
    for p in productos:
        stock_info = f", stock disponible: {p.stock_sede}" if p.stock_sede is not None else ""
        lineas.append(
            f"- {p.nombre} (categoria: {p.categoria_nombre or 'sin categoria'}, "
            f"precio: {p.precio}{stock_info}, similitud: {p.similitud})"
        )
    return "\n".join(lineas)


async def generar_respuesta_agente(mensaje_usuario: str, productos: list[ProductoRecuperado]) -> str:
    contexto = _construir_contexto(productos)

    system_prompt = (
        "Eres el asistente de compras de La Economia, una tienda de abarrotes en Neiva, Colombia. "
        "Responde SIEMPRE en espanol, sin mezclar ningun otro idioma bajo ninguna circunstancia, "
        "incluso al mencionar numeros o precios. De forma breve, amable y natural. "
        "Recomienda unicamente productos que aparezcan en el CONTEXTO. "
        "Si el CONTEXTO indica que no hay productos relevantes, dilo con claridad "
        "y sugiere al cliente reformular su busqueda o consultar el catalogo completo. "
        "Nunca inventes productos, precios o existencias que no esten en el CONTEXTO. "
        "Solo ayudas con compras de la tienda: si la pregunta es de otro tema, dilo con amabilidad y no ofrezcas ayuda con ese tema. "
        "Si el cliente solo saluda, saluda y preguntale que producto busca."
    )

    mensaje_completo = (
        f"CONTEXTO (productos recuperados del catalogo):\n{contexto}\n\n"
        f"PREGUNTA DEL CLIENTE:\n{mensaje_usuario}"
    )

    async with httpx.AsyncClient(timeout=60.0) as cliente:
        respuesta = await cliente.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": mensaje_completo},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                },
            },
        )
        respuesta.raise_for_status()
        return respuesta.json()["message"]["content"]
