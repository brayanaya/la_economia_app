"""
Servicio de generación de embeddings para el pipeline RAG (numeral 10 del
documento de arquitectura). Soporta dos proveedores intercambiables,
seleccionados mediante la variable de entorno EMBEDDING_PROVIDER:

- "openai": usa el modelo text-embedding-3-small de OpenAI, invocado con
  el parámetro `dimensions=768` para producir vectores compatibles con la
  columna `embedding vector(768)` de la tabla embeddings_productos.
- "sentence_transformers": usa un modelo local multilingüe (por defecto
  `paraphrase-multilingual-mpnet-base-v2`, que produce 768 dimensiones de
  forma nativa), útil para desarrollo sin dependencia de una API externa
  de pago y con buen desempeño en español.

Ambos caminos exponen la misma interfaz asíncrona `get_embedding`, de
manera que el resto de la aplicación (retriever, ingesta de catálogo) es
agnóstica al proveedor configurado.
"""
from __future__ import annotations

import asyncio
import functools
from typing import Protocol

from app.core.config import settings


class EmbeddingProvider(Protocol):
    async def embed(self, texto: str) -> list[float]: ...
    async def embed_batch(self, textos: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddingProvider:
    """Genera embeddings mediante la API de OpenAI (text-embedding-3-small)."""

    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        # Import diferido: evita la dependencia dura del paquete `openai`
        # cuando el proyecto se ejecuta con EMBEDDING_PROVIDER=sentence_transformers.
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimensions = dimensions

    async def embed(self, texto: str) -> list[float]:
        resultado = await self.embed_batch([texto])
        return resultado[0]

    async def embed_batch(self, textos: list[str]) -> list[list[float]]:
        respuesta = await self._client.embeddings.create(
            model=self._model,
            input=textos,
            dimensions=self._dimensions,
        )
        # La API devuelve los resultados en el mismo orden que el input.
        return [item.embedding for item in respuesta.data]


class SentenceTransformersEmbeddingProvider:
    """Genera embeddings localmente mediante un modelo de Sentence-Transformers."""

    def __init__(self, model_name: str) -> None:
        # Import diferido: evita cargar torch/sentence-transformers cuando
        # el proyecto se ejecuta con EMBEDDING_PROVIDER=openai.
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    async def embed(self, texto: str) -> list[float]:
        resultado = await self.embed_batch([texto])
        return resultado[0]

    async def embed_batch(self, textos: list[str]) -> list[list[float]]:
        # SentenceTransformer.encode es una llamada síncrona y bloqueante
        # (usa CPU/GPU intensivamente); se delega a un hilo aparte para no
        # bloquear el event loop de FastAPI.
        loop = asyncio.get_running_loop()
        encode_fn = functools.partial(
            self._model.encode,
            textos,
            normalize_embeddings=True,  # requerido para similitud coseno consistente
            convert_to_numpy=True,
        )
        vectores = await loop.run_in_executor(None, encode_fn)
        return [vector.tolist() for vector in vectores]


@functools.lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """Fábrica cacheada del proveedor de embeddings configurado."""
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=openai requiere configurar OPENAI_API_KEY en el .env"
            )
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            dimensions=settings.embedding_dimensions,
        )

    return SentenceTransformersEmbeddingProvider(
        model_name=settings.sentence_transformers_model
    )


async def get_embedding(texto: str) -> list[float]:
    """Punto de entrada único usado por los endpoints y por el retriever."""
    provider = get_embedding_provider()
    return await provider.embed(texto)


def construir_contenido_fuente(
    nombre: str, categoria: str, etiquetas: list[str] | None, descripcion: str | None
) -> str:
    """
    Plantilla de construcción del texto fuente para el embedding de un
    producto, conforme al numeral 10.2 del documento de arquitectura.
    Deliberadamente NO incluye stock ni precio (atributos volátiles).
    """
    etiquetas_texto = ", ".join(etiquetas) if etiquetas else "sin etiquetas"
    return (
        f"Producto: {nombre}\n"
        f"Categoría: {categoria}\n"
        f"Etiquetas: {etiquetas_texto}\n"
        f"Descripción: {descripcion or 'sin descripción adicional'}"
    )
