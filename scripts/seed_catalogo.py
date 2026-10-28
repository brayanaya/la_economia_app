"""
Ingesta idempotente del catálogo de La Economía Aya.

Hace dos cosas:

1. Upsert de sedes, categorías, productos e inventario (los mismos datos de
   db/seed.sql, con ON CONFLICT DO UPDATE para poder re-ejecutarlo sobre una
   base ya creada por docker compose, actualizando precios, imágenes y stock).
2. Generación de embeddings de los productos (tabla embeddings_productos)
   con el proveedor configurado en .env, para que la búsqueda semántica y el
   agente conversacional encuentren todo el catálogo.

Uso (desde la raíz del proyecto, con el venv activo o su binario):

    .venv/bin/python -m scripts.seed_catalogo

Opciones:

    --solo-embeddings   No toca el catálogo; solo regenera embeddings.
    --sin-embeddings    Actualiza el catálogo pero no genera embeddings
                        (útil si el proveedor de embeddings está apagado).

Si el proveedor de embeddings falla (p. ej. Ollama apagado), el catálogo
queda actualizado igual y el script termina con advertencia y código 0:
la búsqueda por texto (/productos/buscar) no depende de embeddings.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.categoria import Categoria
from app.models.embedding import EmbeddingProducto
from app.models.inventario import InventarioSede
from app.models.producto import Producto
from app.models.sede import Sede
from app.services.embeddings import construir_contenido_fuente, get_embedding

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_catalogo")

SEDE_SANTA_ISABEL = "a0000000-0000-0000-0000-000000000001"
SEDE_MACHINES = "a0000000-0000-0000-0000-000000000002"

# (id, nombre, descripcion)
CATEGORIAS = [
    ("b0000000-0000-0000-0000-000000000001", "Granos y abarrotes", "Arroz, fríjol, lentejas, aceites y básicos de despensa"),
    ("b0000000-0000-0000-0000-000000000002", "Lácteos y huevos", "Leche, huevos, quesos, yogures y derivados lácteos"),
    ("b0000000-0000-0000-0000-000000000003", "Cárnicos", "Carnes frescas, pollo y carnes frías"),
    ("b0000000-0000-0000-0000-000000000004", "Frutas y verduras", "Fruver: hortalizas, tubérculos, frutas y verduras frescas"),
    ("b0000000-0000-0000-0000-000000000005", "Panadería", "Panes, arepas y productos de panadería"),
    ("b0000000-0000-0000-0000-000000000006", "Despensa", "Café, chocolate, panela, avena, sal y enlatados"),
    ("b0000000-0000-0000-0000-000000000007", "Bebidas", "Gaseosas, jugos, agua y bebidas frías"),
    ("b0000000-0000-0000-0000-000000000008", "Aseo y hogar", "Detergentes y productos de limpieza"),
    ("b0000000-0000-0000-0000-000000000009", "Cuidado personal", "Jabones, shampoo e higiene personal"),
    ("b0000000-0000-0000-0000-000000000010", "Licores", "Cervezas y bebidas alcohólicas"),
]

ABARROTES = "b0000000-0000-0000-0000-000000000001"
LACTEOS = "b0000000-0000-0000-0000-000000000002"
CARNICOS = "b0000000-0000-0000-0000-000000000003"
FRUVER = "b0000000-0000-0000-0000-000000000004"
PANADERIA = "b0000000-0000-0000-0000-000000000005"
DESPENSA = "b0000000-0000-0000-0000-000000000006"
BEBIDAS = "b0000000-0000-0000-0000-000000000007"
ASEO = "b0000000-0000-0000-0000-000000000008"
CUIDADO = "b0000000-0000-0000-0000-000000000009"
LICORES = "b0000000-0000-0000-0000-000000000010"

# (id, codigo_barras, nombre, descripcion, categoria, precio, saludable, imagen,
#  stock_santa_isabel, stock_machines)  — stock None = no se vende en esa sede.
PRODUCTOS = [
    ("c0000000-0000-0000-0000-000000000001", "7702001001001", "Arroz blanco Diana x 500g",
     "Arroz blanco de grano suelto. Base de la canasta familiar colombiana: ideal para el calentado, acompañamientos y almuerzos diarios.",
     ABARROTES, "3900.00", False, "/img/productos/arroz.svg", 40, 20),
    ("c0000000-0000-0000-0000-000000000002", "7702001002002", "Leche entera Alquería x 1L",
     "Leche entera pasteurizada, fuente de calcio y proteína. Perfecta para el desayuno con chocolate, café o avena.",
     LACTEOS, "4900.00", True, "/img/productos/leche.svg", 24, 10),
    ("c0000000-0000-0000-0000-000000000003", "7702001003003", "Aceite vegetal Gourmet x 500ml",
     "Aceite vegetal mixto apto para frituras, guisos y preparaciones diarias de la cocina.",
     ABARROTES, "7400.00", False, "/img/productos/aceite.svg", 18, 0),
    ("c0000000-0000-0000-0000-000000000004", "7702001004004", "Pechuga de pollo fresca x 500g",
     "Pechuga de pollo fresca, alta en proteína y baja en grasa. Ideal para almuerzos y preparaciones a la plancha.",
     CARNICOS, "13400.00", True, "/img/productos/pollo.svg", 12, 16),
    ("c0000000-0000-0000-0000-000000000005", "7702001005005", "Huevos AA rojos x 30 unidades",
     "Cubeta de 30 huevos rojos AA, frescos de la región. Los infaltables del desayuno: pericos, revueltos o tibios.",
     LACTEOS, "16900.00", True, "/img/productos/huevos.svg", 15, 9),
    ("c0000000-0000-0000-0000-000000000006", "7702001006006", "Fríjol cargamanto x 500g",
     "Fríjol cargamanto santafereño, la base del calentado paisa y de las sopas de la abuela.",
     ABARROTES, "5600.00", True, "/img/productos/frijol.svg", 30, 14),
    ("c0000000-0000-0000-0000-000000000007", "7702001007007", "Lentejas conchas x 500g",
     "Lentejas conchas de grano entero, ricas en hierro y fibra. Clásicas en sopas y guisos caseros.",
     ABARROTES, "4900.00", True, "/img/productos/lentejas.svg", 26, 12),
    ("c0000000-0000-0000-0000-000000000008", "7702001008008", "Arepa blanca x 6 unidades",
     "Arepa blanca asadera, paquete de 6 unidades. La compañera del desayuno con queso, mantequilla o huevos pericos.",
     PANADERIA, "5900.00", True, "/img/productos/arepa.svg", 22, 15),
    ("c0000000-0000-0000-0000-000000000009", "7702001009009", "Pan tajado blanco x 400g",
     "Pan tajado blanco, suave y fresco. Ideal para el desayuno con mantequilla, queso o jamón.",
     PANADERIA, "4300.00", False, "/img/productos/pan.svg", 20, 13),
    ("c0000000-0000-0000-0000-000000000010", "7702001010010", "Chocolate en polvo x 250g",
     "Chocolate en polvo para preparar el chocolate caliente de la tarde o el desayuno con queso y almojábana.",
     DESPENSA, "9800.00", False, "/img/productos/chocolate.svg", 16, 11),
    ("c0000000-0000-0000-0000-000000000011", "7702001011011", "Queso campesino x 500g",
     "Queso campesino fresco, ideal para el desayuno con arepa, para el chocolate caliente o para tostar en sartén.",
     LACTEOS, "12500.00", True, "/img/productos/queso.svg", 14, 8),
    ("c0000000-0000-0000-0000-000000000012", "7702001012012", "Tomate chonto x 500g",
     "Tomate chonto maduro, la base del hogao y de los huevos pericos. Fresco y de la región.",
     FRUVER, "2900.00", True, "/img/productos/tomate.svg", 28, 18),
    ("c0000000-0000-0000-0000-000000000013", "7702001013013", "Cebolla larga junca x 500g",
     "Cebolla larga junca fresca, infaltable en el hogao, los pericos y los guisos colombianos.",
     FRUVER, "2500.00", True, "/img/productos/cebolla-larga.svg", 25, 20),
    ("c0000000-0000-0000-0000-000000000014", "7702001014014", "Sal refinada x 500g",
     "Sal refinada de cocina, para sazonar pericos, sopas y preparaciones del día a día.",
     DESPENSA, "1900.00", False, "/img/productos/sal.svg", 35, 24),
    ("c0000000-0000-0000-0000-000000000015", "7702001015015", "Café tostado molido x 250g",
     "Café tostado molido de origen colombiano. El aromático que abre el desayuno y acompaña las tardes.",
     DESPENSA, "12900.00", False, "/img/productos/cafe.svg", 20, 9),
    ("c0000000-0000-0000-0000-000000000016", "7702001016016", "Panela redonda x 500g",
     "Panela redonda de caña, para el agua de panela caliente con queso o limón. Tradición campesina.",
     DESPENSA, "3800.00", True, "/img/productos/panela.svg", 32, 17),
    ("c0000000-0000-0000-0000-000000000017", "7702001017017", "Plátano hartón x kilo",
     "Plátano hartón fresco, para patacones, cocidos o madurados. Fruta de la región.",
     FRUVER, "3200.00", True, "/img/productos/platano.svg", 24, 15),
    ("c0000000-0000-0000-0000-000000000018", "7702001018018", "Papa criolla x kilo",
     "Papa criolla amarilla, ideal para el calentado, purés y sopas. La papa sabrosa de siempre.",
     FRUVER, "4900.00", True, "/img/productos/papa.svg", 30, 21),
    ("c0000000-0000-0000-0000-000000000019", "7702001019019", "Yuca fresca x kilo",
     "Yuca fresca de la región, para frita, cocida o en sancocho. Compañera del calentado.",
     FRUVER, "3500.00", True, "/img/productos/yuca.svg", 26, 19),
    ("c0000000-0000-0000-0000-000000000020", "7702001020020", "Aguacate hass x 500g",
     "Aguacate hass cremoso, para guacamole, ensaladas o la tajada de las tardes.",
     FRUVER, "6500.00", True, "/img/productos/aguacate.svg", 0, 6),
    ("c0000000-0000-0000-0000-000000000021", "7702001021021", "Jamón de cerro x 250g",
     "Jamón de cerro en láminas, ideal para sánduches, arepas o el desayuno con pan.",
     CARNICOS, "10900.00", False, "/img/productos/jamon.svg", 10, 7),
    ("c0000000-0000-0000-0000-000000000022", "7702001022022", "Avena en hojuelas x 250g",
     "Avena en hojuelas, desayuno saludable con leche, frutas o en avena caliente con panela.",
     DESPENSA, "4200.00", True, "/img/productos/avena.svg", 18, 10),
    ("c0000000-0000-0000-0000-000000000023", "7702001023023", "Yogur natural fresa x 1L",
     "Yogur natural con fresa, fuente de calcio. Desayuno o merienda con granola o avena.",
     LACTEOS, "8900.00", True, "/img/productos/yogur.svg", 12, 6),
    ("c0000000-0000-0000-0000-000000000024", "7702001024024", "Gaseosa cola x 1.5L",
     "Gaseosa tipo cola familiar de 1.5 litros, bien fría para el almuerzo.",
     BEBIDAS, "4700.00", False, "/img/productos/gaseosa.svg", 22, 14),
    ("c0000000-0000-0000-0000-000000000025", "7702001025025", "Cerveza Águila x 6 unidades",
     "Sixpack de cerveza Águila, la preferida para el partido y el asado. Venta prohibida a menores de edad.",
     LICORES, "16900.00", False, "/img/productos/cerveza.svg", 8, None),
    ("c0000000-0000-0000-0000-000000000026", "7702001026026", "Detergente en polvo x 500g",
     "Detergente en polvo de alto rendimiento para ropa blanca y de color.",
     ASEO, "6200.00", False, "/img/productos/detergente.svg", 16, 12),
    ("c0000000-0000-0000-0000-000000000027", "7702001027027", "Jabón de baño x 110g",
     "Jabón de baño humectante para el cuidado diario de la piel.",
     CUIDADO, "2800.00", False, "/img/productos/jabon.svg", 30, 18),
]


async def _upsert_sedes(db: AsyncSession) -> None:
    filas = [
        {"id": uuid.UUID(SEDE_SANTA_ISABEL), "nombre": "Santa Isabel", "direccion": "Calle 10 Sur 21-92, Neiva, Huila"},
        {"id": uuid.UUID(SEDE_MACHINES), "nombre": "Machines", "direccion": "Cra. 52 #26A-13, Neiva, Huila"},
    ]
    for fila in filas:
        stmt = pg_insert(Sede).values(**fila)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Sede.id], set_={"nombre": stmt.excluded.nombre, "direccion": stmt.excluded.direccion}
        )
        await db.execute(stmt)
    logger.info("Sedes listas: %d", len(filas))


async def _upsert_categorias(db: AsyncSession) -> None:
    for id_texto, nombre, descripcion in CATEGORIAS:
        fila = {"id": uuid.UUID(id_texto), "nombre": nombre, "descripcion": descripcion}
        stmt = pg_insert(Categoria).values(**fila)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Categoria.id],
            set_={"nombre": stmt.excluded.nombre, "descripcion": stmt.excluded.descripcion},
        )
        await db.execute(stmt)
    logger.info("Categorías listas: %d", len(CATEGORIAS))


async def _upsert_productos_e_inventario(db: AsyncSession) -> None:
    for (id_texto, codigo, nombre, descripcion, categoria, precio, saludable, imagen,
         stock_si, stock_ma) in PRODUCTOS:
        fila = {
            "id": uuid.UUID(id_texto),
            "codigo_barras": codigo,
            "nombre": nombre,
            "descripcion": descripcion,
            "categoria_id": uuid.UUID(categoria),
            "precio_venta": Decimal(precio),
            "es_saludable": saludable,
            "imagen_url": imagen,
        }
        stmt = pg_insert(Producto).values(**fila)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Producto.id],
            set_={
                "codigo_barras": stmt.excluded.codigo_barras,
                "nombre": stmt.excluded.nombre,
                "descripcion": stmt.excluded.descripcion,
                "categoria_id": stmt.excluded.categoria_id,
                "precio_venta": stmt.excluded.precio_venta,
                "es_saludable": stmt.excluded.es_saludable,
                "imagen_url": stmt.excluded.imagen_url,
            },
        )
        await db.execute(stmt)

        inventarios = [
            (SEDE_SANTA_ISABEL, stock_si),
            (SEDE_MACHINES, stock_ma),
        ]
        for sede_id, stock in inventarios:
            if stock is None:
                continue
            fila_inv = {
                "producto_id": uuid.UUID(id_texto),
                "sede_id": uuid.UUID(sede_id),
                "stock_actual": stock,
                "stock_minimo": 4,
            }
            stmt_inv = pg_insert(InventarioSede).values(**fila_inv)
            stmt_inv = stmt_inv.on_conflict_do_update(
                index_elements=[InventarioSede.producto_id, InventarioSede.sede_id],
                set_={"stock_actual": stmt_inv.excluded.stock_actual, "stock_minimo": stmt_inv.excluded.stock_minimo},
            )
            await db.execute(stmt_inv)
    logger.info("Productos listos: %d (con inventario por sede)", len(PRODUCTOS))


async def _generar_embeddings(db: AsyncSession) -> bool:
    """
    Regenera el embedding de cada producto. Devuelve False si el proveedor
    de embeddings no está disponible (el catálogo queda igualmente actualizado).
    """
    categorias = {
        categoria.id: categoria.nombre
        for categoria in (await db.execute(select(Categoria))).scalars()
    }
    productos = (await db.execute(select(Producto).order_by(Producto.nombre))).scalars().all()
    logger.info("Generando embeddings para %d productos…", len(productos))
    generados = 0
    try:
        for producto in productos:
            contenido = construir_contenido_fuente(
                producto.nombre,
                categorias.get(producto.categoria_id, ""),
                [],
                producto.descripcion,
            )
            vector = await get_embedding(contenido, tipo="document")
            await db.execute(delete(EmbeddingProducto).where(EmbeddingProducto.producto_id == producto.id))
            db.add(EmbeddingProducto(producto_id=producto.id, contenido_textual=contenido, embedding=vector))
            generados += 1
    except Exception as exc:  # noqa: BLE001 - degradación controlada
        logger.warning(
            "No se pudieron generar los embeddings (%s). La búsqueda por texto funciona, "
            "la semántica necesita el proveedor de embeddings activo (p. ej. Ollama encendido).",
            exc,
        )
        return False
    logger.info("Embeddings generados: %d", generados)
    return generados == len(productos)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Ingesta idempotente del catálogo con embeddings")
    parser.add_argument("--solo-embeddings", action="store_true", help="No tocar el catálogo, solo embeddings")
    parser.add_argument("--sin-embeddings", action="store_true", help="Solo catálogo, sin embeddings")
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        if not args.solo_embeddings:
            await _upsert_sedes(db)
            await _upsert_categorias(db)
            await _upsert_productos_e_inventario(db)
            await db.commit()
            logger.info("Catálogo actualizado ✔")
        if not args.sin_embeddings:
            ok = await _generar_embeddings(db)
            await db.commit()
            if not ok:
                return 0
    logger.info("Listo ✔")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
