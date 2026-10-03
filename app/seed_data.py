import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.categoria import Categoria
from app.models.embedding import EmbeddingProducto
from app.models.inventario import InventarioSede
from app.models.producto import Producto
from app.models.sede import Sede
from app.services.embeddings import get_embedding

SEED_CATEGORIAS = [
    {"nombre": "Café y Desayuno", "descripcion": "Café molido, soluble, chocolate y cereales"},
]

SEED_PRODUCTOS = [
    {
        "codigo_barras": "7702001006006",
        "nombre": "Café Sello Rojo Molido 500g",
        "descripcion": "Café tostado y molido de molienda media, aroma intenso y sabor tradicional colombiano.",
        "precio_venta": 18500.00,
        "es_saludable": False,
        "categoria": "Café y Desayuno",
        "stock_santa_isabel": 45,
        "stock_machines": 30,
    },
    {
        "codigo_barras": "7702001007007",
        "nombre": "Café Águila Roja 250g",
        "descripcion": "Café molido tradicional de excelente aroma y cuerpo.",
        "precio_venta": 9800.00,
        "es_saludable": False,
        "categoria": "Café y Desayuno",
        "stock_santa_isabel": 60,
        "stock_machines": 50,
    },
    {
        "codigo_barras": "7702001008008",
        "nombre": "Chocolate Corona Pasta 500g",
        "descripcion": "Chocolate para mesa tradicional con clavo y canela.",
        "precio_venta": 8900.00,
        "es_saludable": False,
        "categoria": "Café y Desayuno",
        "stock_santa_isabel": 50,
        "stock_machines": 40,
    },
]


async def ejecutar_seed():
    async with AsyncSessionLocal() as session:
        print("Iniciando seed incremental de catalogo...")

        # Sedes: ya existen desde db/seed.sql (Santa Isabel, Machines); solo se consultan.
        mapa_sedes = {}
        for nombre_sede in ("Santa Isabel", "Machines"):
            res = await session.execute(select(Sede).where(Sede.nombre == nombre_sede))
            sede = res.scalars().first()
            if not sede:
                raise RuntimeError(f"No se encontro la sede '{nombre_sede}'. Revisa db/seed.sql.")
            mapa_sedes[nombre_sede] = sede.id

        # Categorias: crea las que falten (ej. 'Cafe y Desayuno' no existe aun).
        mapa_categorias = {}
        for c_data in SEED_CATEGORIAS:
            res = await session.execute(select(Categoria).where(Categoria.nombre == c_data["nombre"]))
            cat = res.scalars().first()
            if not cat:
                cat = Categoria(nombre=c_data["nombre"], descripcion=c_data["descripcion"])
                session.add(cat)
                await session.flush()
                print(f"Categoria creada: {cat.nombre}")
            mapa_categorias[c_data["nombre"]] = cat.id

        # Productos + embeddings + inventario por sede
        for p_data in SEED_PRODUCTOS:
            res = await session.execute(
                select(Producto).where(Producto.codigo_barras == p_data["codigo_barras"])
            )
            if res.scalars().first():
                print(f"Ya existe, se omite: {p_data['nombre']}")
                continue

            prod = Producto(
                codigo_barras=p_data["codigo_barras"],
                nombre=p_data["nombre"],
                descripcion=p_data["descripcion"],
                precio_venta=p_data["precio_venta"],
                es_saludable=p_data["es_saludable"],
                categoria_id=mapa_categorias[p_data["categoria"]],
            )
            session.add(prod)
            await session.flush()

            texto_contenido = (
                f"{p_data['nombre']}. {p_data['descripcion']}. Categoria: {p_data['categoria']}."
            )
            vector = await get_embedding(texto_contenido)

            session.add(
                EmbeddingProducto(
                    producto_id=prod.id,
                    contenido_textual=texto_contenido,
                    embedding=vector,
                )
            )

            session.add_all([
                InventarioSede(
                    producto_id=prod.id,
                    sede_id=mapa_sedes["Santa Isabel"],
                    stock_actual=p_data["stock_santa_isabel"],
                    stock_minimo=5,
                ),
                InventarioSede(
                    producto_id=prod.id,
                    sede_id=mapa_sedes["Machines"],
                    stock_actual=p_data["stock_machines"],
                    stock_minimo=5,
                ),
            ])

            print(f"Producto sembrado: {prod.nombre}")

        await session.commit()
        print("Seed incremental completado.")


if __name__ == "__main__":
    asyncio.run(ejecutar_seed())
