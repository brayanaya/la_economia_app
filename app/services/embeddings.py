"""
Servicio de generación de embeddings para el pipeline RAG (numeral 10 del
documento de arquitectura). Soporta tres proveedores intercambiables,
seleccionados mediante la variable de entorno EMBEDDING_PROVIDER:

- "ollama": usa un modelo de embeddings servido por Ollama local (por
  defecto `nomic-embed-text`, 768 dimensiones nativas). No requiere torch,
  por lo que evita bloqueos de DLL en Windows.
- "openai": usa el modelo text-embedding-3-small de OpenAI, invocado con
  el parámetro `dimensions=768` para producir vectores compatibles con la
  columna `embedding vector(768)` de la tabla embeddings_productos.
- "sentence_transformers": usa un modelo local multilingüe (por defecto
  `paraphrase-multilingual-mpnet-base-v2`, 768 dimensiones), útil cuando
  torch está disponible en el equipo.

Todos exponen la misma interfaz asíncrona `get_embedding`, de manera que el
resto de la aplicación (retriever, ingesta de catálogo) es agnóstica al
proveedor configurado.

IMPORTANTE: los vectores de modelos distintos NO son comparables entre sí.
Al cambiar de proveedor hay que regenerar todos los embeddings del catálogo.
"""
from __future__ import annotations

import asyncio
import functools
from typing import Literal, Protocol

import httpx

from app.core.config import settings


class EmbeddingProvider(Protocol):
    async def embed(self, texto: str) -> list[float]: ...
    async def embed_batch(self, textos: list[str]) -> list[list[float]]: ...


class OllamaEmbeddingProvider:
    """Genera embeddings mediante la API local de Ollama (/api/embed)."""

    def __init__(self, base_url: str, model: str, dimensions: int) -> None:
        self._url = f"{base_url.rstrip('/')}/api/embed"
        self._model = model
        self._dimensions = dimensions

    async def embed(self, texto: str) -> list[float]:
        resultado = await self.embed_batch([texto])
        return resultado[0]

    async def embed_batch(self, textos: list[str]) -> list[list[float]]:
        # Timeout holgado: la primera llamada carga el modelo en memoria.
        async with httpx.AsyncClient(timeout=120.0) as client:
            respuesta = await client.post(
                self._url,
                json={"model": self._model, "input": textos},
            )
            respuesta.raise_for_status()
        vectores = respuesta.json()["embeddings"]
        for vector in vectores:
            if len(vector) != self._dimensions:
                raise RuntimeError(
                    f"El modelo '{self._model}' devolvió {len(vector)} dimensiones, "
                    f"pero la columna vector({self._dimensions}) espera {self._dimensions}."
                )
        return vectores


class OpenAIEmbeddingProvider:
    """Genera embeddings mediante la API de OpenAI (text-embedding-3-small)."""

    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        # Import diferido: evita la dependencia dura del paquete `openai`
        # cuando el proyecto se ejecuta con otro proveedor.
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
        # el proyecto se ejecuta con otro proveedor.
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
    proveedor = settings.embedding_provider

    if proveedor == "openai":
        if not settings.openai_api_key:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=openai requiere configurar OPENAI_API_KEY en el .env"
            )
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            dimensions=settings.embedding_dimensions,
        )

    if proveedor == "sentence_transformers":
        return SentenceTransformersEmbeddingProvider(
            model_name=settings.sentence_transformers_model
        )

    # Por defecto: Ollama (no depende de torch).
    return OllamaEmbeddingProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embedding_model,
        dimensions=settings.embedding_dimensions,
    )


def _aplicar_prefijo(texto: str, tipo: str) -> str:
    """Nomic Embed necesita prefijos de tarea distintos para consulta y documento."""
    if settings.embedding_provider != "ollama":
        return texto
    if not settings.ollama_embedding_model.startswith("nomic-embed-text"):
        return texto
    prefijo = "search_query: " if tipo == "query" else "search_document: "
    return texto if texto.startswith(prefijo) else prefijo + texto


async def get_embedding(
    texto: str, tipo: Literal["query", "document"] = "query"
) -> list[float]:
    """Punto de entrada único usado por los endpoints y por el retriever."""
    provider = get_embedding_provider()
    return await provider.embed(_aplicar_prefijo(texto, tipo))


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