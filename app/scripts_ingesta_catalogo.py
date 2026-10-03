"""
Script de ingesta del catálogo hacia embeddings_productos.

Recorre todos los productos activos, construye su texto fuente (plantilla
del numeral 10.2) y genera su embedding mediante el proveedor configurado
en EMBEDDING_PROVIDER, insertándolo (o actualizándolo) en la tabla
embeddings_productos.

Ejecución local (con el entorno virtual activado):
    python -m app.scripts_ingesta_catalogo

Este script es idempotente: si un producto ya tiene un embedding vigente,
lo reemplaza en lugar de duplicarlo.
"""
import asyncio

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.categoria import Categoria
from app.models.embedding import EmbeddingProducto
from app.models.producto import Producto
from app.services.embeddings import construir_contenido_fuente, get_embedding


async def ingestar_catalogo() -> None:
    async with AsyncSessionLocal() as db:
        stmt = select(Producto)
        productos = (await db.execute(stmt)).scalars().all()

        print(f"Productos encontrados para indexar: {len(productos)}")

        for producto in productos:
            categoria = await db.get(Categoria, producto.categoria_id)
            etiquetas = ["saludable"] if producto.es_saludable else []

            contenido = construir_contenido_fuente(
                nombre=producto.nombre,
                categoria=categoria.nombre if categoria else "Sin categoría",
                etiquetas=etiquetas,
                descripcion=producto.descripcion,
            )

            vector = await get_embedding(contenido)

            # Reemplaza cualquier embedding previo del mismo producto
            # (reindexación incremental ante alta/modificación, RF-09).
            await db.execute(
                delete(EmbeddingProducto).where(EmbeddingProducto.producto_id == producto.id)
            )
            db.add(
                EmbeddingProducto(
                    producto_id=producto.id,
                    contenido_textual=contenido,
                    embedding=vector,
                )
            )
            print(f"  ✓ Indexado: {producto.nombre}")

        await db.commit()
        print("Ingesta completada.")


if __name__ == "__main__":
    asyncio.run(ingestar_catalogo())
