"""
Fixtures de catálogo MOCK para desarrollo y testing.

⚠️  IMPORTANTE: Estos datos son FICTICIOS y SOLO para desarrollo/testing.
    NO representan el catálogo real de MasControl.
    Cada producto tiene fuente="fixture_desarrollo" para identificación clara.
"""
from datetime import datetime
from typing import Dict, List
import random

from app.services.providers.base import Producto, Promocion


# ============================================================
# DATOS FIXTURE - PRODUCTOS COLOMBIANOS REALISTAS (FICTICIOS)
# ============================================================

MOCK_CATEGORIAS = {
    "cat_001": {"id": "cat_001", "nombre": "Frutas y Verduras"},
    "cat_002": {"id": "cat_002", "nombre": "Carnes y Pescados"},
    "cat_003": {"id": "cat_003", "nombre": "Lácteos y Huevos"},
    "cat_004": {"id": "cat_004", "nombre": "Despensa"},
    "cat_005": {"id": "cat_005", "nombre": "Bebidas"},
    "cat_006": {"id": "cat_006", "nombre": "Snacks y Dulces"},
    "cat_007": {"id": "cat_007", "nombre": "Limpieza y Hogar"},
    "cat_008": {"id": "cat_008", "nombre": "Cuidado Personal"},
    "cat_009": {"id": "cat_009", "nombre": "Mascotas"},
    "cat_010": {"id": "cat_010", "nombre": "Panadería"},
}

# UUIDs fijos para sedes de prueba (compatibles con schema UUID)
MOCK_SEDE_UUID_1 = "a0000000-0000-0000-0000-000000000001"
MOCK_SEDE_UUID_2 = "a0000000-0000-0000-0000-000000000002"

MOCK_SEDES = {
    MOCK_SEDE_UUID_1: {"id": MOCK_SEDE_UUID_1, "nombre": "Sede Principal - Centro"},
    MOCK_SEDE_UUID_2: {"id": MOCK_SEDE_UUID_2, "nombre": "Sede Norte - CC Parque"},
}


def crear_productos_fixture() -> Dict[str, Producto]:
    """Crea el diccionario de productos fixture."""
    fixtures_data = [
        # Frutas y Verduras
        {
            "id": "prod_001", "sku": "FRU-MAN-001", "nombre": "Mango Tommy Atkins",
            "descripcion": "Mango maduro, dulce y jugoso. Ideal para postres y jugos.",
            "descripcion_corta": "Mango maduro y dulce",
            "categoria_id": "cat_001", "categoria_nombre": "Frutas y Verduras",
            "marca": "Fruticola del Caribe", "imagen_url": "/images/mango.jpg",
            "precio_base": 3500, "precio_final": 3500, "tiene_promocion": False,
            "unidad_medida": "unidad", "contenido_neto": 1, "presentacion": "Unidad (~300g)",
            "codigo_barras": "7701234567890", "etiquetas": ["fruta", "tropical", "vitamina_c"],
            "ingredientes_receta": ["mango"],
        },
        {
            "id": "prod_002", "sku": "FRU-PLA-001", "nombre": "Plátano Maduro",
            "descripcion": "Plátano maduro para freír, hornear o postres.",
            "descripcion_corta": "Plátano maduro para cocinar",
            "categoria_id": "cat_001", "categoria_nombre": "Frutas y Verduras",
            "marca": "Banacol", "imagen_url": "/images/platano.jpg",
            "precio_base": 1200, "precio_final": 1200, "tiene_promocion": False,
            "unidad_medida": "unidad", "contenido_neto": 1, "presentacion": "Unidad (~200g)",
            "codigo_barras": "7701234567891", "etiquetas": ["plátano", "cocina", "postre"],
            "ingredientes_receta": ["plátano maduro"],
        },
        {
            "id": "prod_003", "sku": "VER-CEB-001", "nombre": "Cebolla Cabeza Roja",
            "descripcion": "Cebolla roja dulce, ideal para ensaladas y guisos.",
            "descripcion_corta": "Cebolla roja dulce",
            "categoria_id": "cat_001", "categoria_nombre": "Frutas y Verduras",
            "marca": "Hortalizas del Valle", "imagen_url": "/images/cebolla_roja.jpg",
            "precio_base": 2800, "precio_final": 2800, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Kilogramo",
            "codigo_barras": "7701234567892", "etiquetas": ["cebolla", "verdura", "guiso"],
            "ingredientes_receta": ["cebolla", "cebolla roja"],
        },
        {
            "id": "prod_004", "sku": "VER-TOM-001", "nombre": "Tomate Chonto",
            "descripcion": "Tomate chonto maduro, jugoso, para salsas y ensaladas.",
            "descripcion_corta": "Tomate chonto maduro",
            "categoria_id": "cat_001", "categoria_nombre": "Frutas y Verduras",
            "marca": "Agrofrutas", "imagen_url": "/images/tomate.jpg",
            "precio_base": 4500, "precio_final": 4500, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Kilogramo",
            "codigo_barras": "7701234567893", "etiquetas": ["tomate", "salsa", "ensalada"],
            "ingredientes_receta": ["tomate", "tomate chonto"],
        },
        {
            "id": "prod_005", "sku": "VER-AJI-001", "nombre": "Ají Picante",
            "descripcion": "Ají picante fresco para salsas y adobos.",
            "descripcion_corta": "Ají picante fresco",
            "categoria_id": "cat_001", "categoria_nombre": "Frutas y Verduras",
            "marca": "Cultivos del Sol", "imagen_url": "/images/aji.jpg",
            "precio_base": 8000, "precio_final": 8000, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Kilogramo",
            "codigo_barras": "7701234567894", "etiquetas": ["ají", "picante", "salsa"],
            "ingredientes_receta": ["ají", "ají picante"],
        },
        {
            "id": "prod_006", "sku": "FRU-AGU-001", "nombre": "Aguacate Hass",
            "descripcion": "Aguacate Hass maduro, cremoso, ideal para guacamole.",
            "descripcion_corta": "Aguacate Hass maduro",
            "categoria_id": "cat_001", "categoria_nombre": "Frutas y Verduras",
            "marca": "Aguacates de Colombia", "imagen_url": "/images/aguacate.jpg",
            "precio_base": 4200, "precio_final": 4200, "tiene_promocion": False,
            "unidad_medida": "unidad", "contenido_neto": 1, "presentacion": "Unidad (~200g)",
            "codigo_barras": "7701234567895", "etiquetas": ["aguacate", "guacamole", "saludable"],
            "ingredientes_receta": ["aguacate", "aguacate hass"],
        },
        {
            "id": "prod_007", "sku": "VER-CIL-001", "nombre": "Cilantro Fresco",
            "descripcion": "Cilantro fresco aromático para sopas y guisos.",
            "descripcion_corta": "Cilantro fresco",
            "categoria_id": "cat_001", "categoria_nombre": "Frutas y Verduras",
            "marca": "Hierbas del Campo", "imagen_url": "/images/cilantro.jpg",
            "precio_base": 1500, "precio_final": 1500, "tiene_promocion": False,
            "unidad_medida": "atado", "contenido_neto": 1, "presentacion": "Atado (~50g)",
            "codigo_barras": "7701234567896", "etiquetas": ["cilantro", "hierba", "sopa"],
            "ingredientes_receta": ["cilantro"],
        },
        # Carnes y Pescados
        {
            "id": "prod_008", "sku": "CAR-POL-001", "nombre": "Pechuga de Pollo",
            "descripcion": "Pechuga de pollo fresca, sin hueso, sin piel.",
            "descripcion_corta": "Pechuga de pollo fresca",
            "categoria_id": "cat_002", "categoria_nombre": "Carnes y Pescados",
            "marca": "Avícola Nacional", "imagen_url": "/images/pechuga_pollo.jpg",
            "precio_base": 14500, "precio_final": 14500, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Kilogramo",
            "codigo_barras": "7701234567897", "etiquetas": ["pollo", "pechuga", "proteína"],
            "ingredientes_receta": ["pollo", "pechuga de pollo"],
        },
        {
            "id": "prod_009", "sku": "CAR-RES-001", "nombre": "Carne de Res Molida",
            "descripcion": "Carne de res molida magra, ideal para albóndigas y salsas.",
            "descripcion_corta": "Carne molida magra",
            "categoria_id": "cat_002", "categoria_nombre": "Carnes y Pescados",
            "marca": "Frigorífico Andes", "imagen_url": "/images/carne_molida.jpg",
            "precio_base": 18000, "precio_final": 18000, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Kilogramo",
            "codigo_barras": "7701234567898", "etiquetas": ["res", "molida", "carne"],
            "ingredientes_receta": ["carne molida", "carne de res"],
        },
        {
            "id": "prod_010", "sku": "PES-TIL-001", "nombre": "Tilapia Fresca",
            "descripcion": "Filete de tilapia fresco, sin espinas, piel opcional.",
            "descripcion_corta": "Filete de tilapia",
            "categoria_id": "cat_002", "categoria_nombre": "Carnes y Pescados",
            "marca": "Acuícola del Magdalena", "imagen_url": "/images/tilapia.jpg",
            "precio_base": 22000, "precio_final": 22000, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Kilogramo",
            "codigo_barras": "7701234567899", "etiquetas": ["pescado", "tilapia", "filete"],
            "ingredientes_receta": ["tilapia", "pescado"],
        },
        # Lácteos y Huevos
        {
            "id": "prod_011", "sku": "LAC-LEC-001", "nombre": "Leche Entera Alpina",
            "descripcion": "Leche entera pasteurizada, 1 litro.",
            "descripcion_corta": "Leche entera 1L",
            "categoria_id": "cat_003", "categoria_nombre": "Lácteos y Huevos",
            "marca": "Alpina", "imagen_url": "/images/leche_alpina.jpg",
            "precio_base": 4800, "precio_final": 4800, "tiene_promocion": False,
            "unidad_medida": "litro", "contenido_neto": 1, "presentacion": "Bolsa 1 Litro",
            "codigo_barras": "7701234567900", "etiquetas": ["leche", "entera", "lácteo"],
            "ingredientes_receta": ["leche", "leche entera"],
        },
        {
            "id": "prod_012", "sku": "LAC-QUE-001", "nombre": "Queso Doble Crema",
            "descripcion": "Queso doble crema, suave y cremoso.",
            "descripcion_corta": "Queso doble crema",
            "categoria_id": "cat_003", "categoria_nombre": "Lácteos y Huevos",
            "marca": "Colanta", "imagen_url": "/images/queso_doble_crema.jpg",
            "precio_base": 16500, "precio_final": 16500, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Kilogramo",
            "codigo_barras": "7701234567901", "etiquetas": ["queso", "doble crema", "lácteo"],
            "ingredientes_receta": ["queso", "queso doble crema"],
        },
        {
            "id": "prod_013", "sku": "LAC-HUE-001", "nombre": "Huevos AAA x12",
            "descripcion": "Huevos categoria AAA, docena.",
            "descripcion_corta": "Huevos AAA docena",
            "categoria_id": "cat_003", "categoria_nombre": "Lácteos y Huevos",
            "marca": "Avícola La Esperanza", "imagen_url": "/images/huevos.jpg",
            "precio_base": 9800, "precio_final": 9800, "tiene_promocion": False,
            "unidad_medida": "docena", "contenido_neto": 12, "presentacion": "Cartón x12 unidades",
            "codigo_barras": "7701234567902", "etiquetas": ["huevos", "proteína", "desayuno"],
            "ingredientes_receta": ["huevo", "huevos"],
        },
        {
            "id": "prod_014", "sku": "LAC-YOG-001", "nombre": "Yogur Griego Natural",
            "descripcion": "Yogur griego natural sin azúcar, 170g.",
            "descripcion_corta": "Yogur griego 170g",
            "categoria_id": "cat_003", "categoria_nombre": "Lácteos y Huevos",
            "marca": "Alquería", "imagen_url": "/images/yogur_griego.jpg",
            "precio_base": 3200, "precio_final": 3200, "tiene_promocion": False,
            "unidad_medida": "unidad", "contenido_neto": 170, "presentacion": "Tarro 170g",
            "codigo_barras": "7701234567903", "etiquetas": ["yogur", "griego", "proteína"],
            "ingredientes_receta": ["yogur", "yogur griego"],
        },
        # Despensa
        {
            "id": "prod_015", "sku": "DES-ARR-001", "nombre": "Arroz Blanco Supremo",
            "descripcion": "Arroz blanco grano largo, calidad suprema.",
            "descripcion_corta": "Arroz supremo 1kg",
            "categoria_id": "cat_004", "categoria_nombre": "Despensa",
            "marca": "Roa", "imagen_url": "/images/arroz.jpg",
            "precio_base": 4200, "precio_final": 4200, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Bolsa 1kg",
            "codigo_barras": "7701234567904", "etiquetas": ["arroz", "granos", "base"],
            "ingredientes_receta": ["arroz", "arroz blanco"],
        },
        {
            "id": "prod_016", "sku": "DES-FRI-001", "nombre": "Fríjol Rojo Cargamanto",
            "descripcion": "Fríjol rojo cargamanto, grano seleccionado.",
            "descripcion_corta": "Fríjol cargamanto 500g",
            "categoria_id": "cat_004", "categoria_nombre": "Despensa",
            "marca": "La Constancia", "imagen_url": "/images/frijol.jpg",
            "precio_base": 5800, "precio_final": 5800, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 0.5, "presentacion": "Bolsa 500g",
            "codigo_barras": "7701234567905", "etiquetas": ["fríjol", "legumbre", "proteína"],
            "ingredientes_receta": ["fríjol", "fríjol rojo", "cargamanto"],
        },
        {
            "id": "prod_017", "sku": "DES-ACE-001", "nombre": "Aceite de Girasol",
            "descripcion": "Aceite de girasol refinado, 1 litro.",
            "descripcion_corta": "Aceite girasol 1L",
            "categoria_id": "cat_004", "categoria_nombre": "Despensa",
            "marca": "Gourmet", "imagen_url": "/images/aceite.jpg",
            "precio_base": 12500, "precio_final": 12500, "tiene_promocion": False,
            "unidad_medida": "litro", "contenido_neto": 1, "presentacion": "Botella 1 Litro",
            "codigo_barras": "7701234567906", "etiquetas": ["aceite", "girasol", "cocina"],
            "ingredientes_receta": ["aceite", "aceite de girasol"],
        },
        {
            "id": "prod_018", "sku": "DES-SAL-001", "nombre": "Sal Marina",
            "descripcion": "Sal marina gruesa, natural.",
            "descripcion_corta": "Sal marina 500g",
            "categoria_id": "cat_004", "categoria_nombre": "Despensa",
            "marca": "Salina", "imagen_url": "/images/sal.jpg",
            "precio_base": 2200, "precio_final": 2200, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 0.5, "presentacion": "Bolsa 500g",
            "codigo_barras": "7701234567907", "etiquetas": ["sal", "marina", "condimento"],
            "ingredientes_receta": ["sal"],
        },
        {
            "id": "prod_019", "sku": "DES-AZU-001", "nombre": "Azúcar Morena",
            "descripcion": "Azúcar morena de caña, 1kg.",
            "descripcion_corta": "Azúcar morena 1kg",
            "categoria_id": "cat_004", "categoria_nombre": "Despensa",
            "marca": "Manuelita", "imagen_url": "/images/azucar.jpg",
            "precio_base": 3800, "precio_final": 3800, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Bolsa 1kg",
            "codigo_barras": "7701234567908", "etiquetas": ["azúcar", "morena", "caña"],
            "ingredientes_receta": ["azúcar", "azúcar morena"],
        },
        {
            "id": "prod_020", "sku": "DES-HAR-001", "nombre": "Harina de Trigo",
            "descripcion": "Harina de trigo todo uso, 1kg.",
            "descripcion_corta": "Harina trigo 1kg",
            "categoria_id": "cat_004", "categoria_nombre": "Despensa",
            "marca": "Harimsa", "imagen_url": "/images/harina.jpg",
            "precio_base": 3200, "precio_final": 3200, "tiene_promocion": False,
            "unidad_medida": "kg", "contenido_neto": 1, "presentacion": "Bolsa 1kg",
            "codigo_barras": "7701234567909", "etiquetas": ["harina", "trigo", "repostería"],
            "ingredientes_receta": ["harina", "harina de trigo"],
        },
        # Bebidas
        {
            "id": "prod_021", "sku": "BEB-AGU-001", "nombre": "Agua Mineral Natural",
            "descripcion": "Agua mineral natural sin gas, 600ml.",
            "descripcion_corta": "Agua mineral 600ml",
            "categoria_id": "cat_005", "categoria_nombre": "Bebidas",
            "marca": "Bristol", "imagen_url": "/images/agua.jpg",
            "precio_base": 2500, "precio_final": 2500, "tiene_promocion": False,
            "unidad_medida": "ml", "contenido_neto": 600, "presentacion": "Botella 600ml",
            "codigo_barras": "7701234567910", "etiquetas": ["agua", "mineral", "hidratación"],
            "ingredientes_receta": ["agua"],
        },
        {
            "id": "prod_022", "sku": "BEB-JUG-001", "nombre": "Jugo de Naranja Natural",
            "descripcion": "Jugo de naranja 100% natural, sin azúcar añadida, 1L.",
            "descripcion_corta": "Jugo naranja 1L",
            "categoria_id": "cat_005", "categoria_nombre": "Bebidas",
            "marca": "Postobón", "imagen_url": "/images/jugo_naranja.jpg",
            "precio_base": 5800, "precio_final": 5800, "tiene_promocion": False,
            "unidad_medida": "litro", "contenido_neto": 1, "presentacion": "Botella 1 Litro",
            "codigo_barras": "7701234567911", "etiquetas": ["jugo", "naranja", "vitamina_c"],
            "ingredientes_receta": ["jugo de naranja", "naranja"],
        },
        {
            "id": "prod_023", "sku": "BEB-GAS-001", "nombre": "Gaseosa Colombiana",
            "descripcion": "Gaseosa sabor kola champagne, 1.5L.",
            "descripcion_corta": "Gaseosa kola 1.5L",
            "categoria_id": "cat_005", "categoria_nombre": "Bebidas",
            "marca": "Postobón", "imagen_url": "/images/gaseosa.jpg",
            "precio_base": 4500, "precio_final": 4500, "tiene_promocion": False,
            "unidad_medida": "litro", "contenido_neto": 1.5, "presentacion": "Botella 1.5 Litros",
            "codigo_barras": "7701234567912", "etiquetas": ["gaseosa", "kola", "champagne"],
            "ingredientes_receta": [],
        },
        # Snacks y Dulces
        {
            "id": "prod_024", "sku": "SNA-CHA-001", "nombre": "Chocolate Colombiano",
            "descripcion": "Chocolate de mesa tradicional, 200g.",
            "descripcion_corta": "Chocolate mesa 200g",
            "categoria_id": "cat_006", "categoria_nombre": "Snacks y Dulces",
            "marca": "Corona", "imagen_url": "/images/chocolate.jpg",
            "precio_base": 6200, "precio_final": 6200, "tiene_promocion": False,
            "unidad_medida": "g", "contenido_neto": 200, "presentacion": "Barra 200g",
            "codigo_barras": "7701234567913", "etiquetas": ["chocolate", "mesa", "tradicional"],
            "ingredientes_receta": ["chocolate", "chocolate de mesa"],
        },
        {
            "id": "prod_025", "sku": "SNA-GAL-001", "nombre": "Galletas de Avena",
            "descripcion": "Galletas de avena con pasas, paquete 300g.",
            "descripcion_corta": "Galletas avena 300g",
            "categoria_id": "cat_006", "categoria_nombre": "Snacks y Dulces",
            "marca": "Festival", "imagen_url": "/images/galletas_avena.jpg",
            "precio_base": 4800, "precio_final": 4800, "tiene_promocion": False,
            "unidad_medida": "g", "contenido_neto": 300, "presentacion": "Paquete 300g",
            "codigo_barras": "7701234567914", "etiquetas": ["galletas", "avena", "pasas"],
            "ingredientes_receta": ["galletas", "avena"],
        },
        # Limpieza y Hogar
        {
            "id": "prod_026", "sku": "LIM-DET-001", "nombre": "Detergente Líquido",
            "descripcion": "Detergente líquido para ropa, 3.8L.",
            "descripcion_corta": "Detergente líquido 3.8L",
            "categoria_id": "cat_007", "categoria_nombre": "Limpieza y Hogar",
            "marca": "Fabuloso", "imagen_url": "/images/detergente.jpg",
            "precio_base": 28000, "precio_final": 28000, "tiene_promocion": False,
            "unidad_medida": "litro", "contenido_neto": 3.8, "presentacion": "Botella 3.8 Litros",
            "codigo_barras": "7701234567915", "etiquetas": ["detergente", "ropa", "líquido"],
            "ingredientes_receta": [],
        },
        # Cuidado Personal
        {
            "id": "prod_027", "sku": "CUI-SHA-001", "nombre": "Shampoo Anticaspa",
            "descripcion": "Shampoo anticaspa, 400ml.",
            "descripcion_corta": "Shampoo anticaspa 400ml",
            "categoria_id": "cat_008", "categoria_nombre": "Cuidado Personal",
            "marca": "Head & Shoulders", "imagen_url": "/images/shampoo.jpg",
            "precio_base": 18500, "precio_final": 18500, "tiene_promocion": False,
            "unidad_medida": "ml", "contenido_neto": 400, "presentacion": "Botella 400ml",
            "codigo_barras": "7701234567916", "etiquetas": ["shampoo", "anticaspa", "cabello"],
            "ingredientes_receta": [],
        },
        # Panadería
        {
            "id": "prod_028", "sku": "PAN-PAN-001", "nombre": "Pan Francés",
            "descripcion": "Pan francés fresco, unidad.",
            "descripcion_corta": "Pan francés unidad",
            "categoria_id": "cat_010", "categoria_nombre": "Panadería",
            "marca": "Panadería La Económica", "imagen_url": "/images/pan_frances.jpg",
            "precio_base": 1200, "precio_final": 1200, "tiene_promocion": False,
            "unidad_medida": "unidad", "contenido_neto": 1, "presentacion": "Unidad (~80g)",
            "codigo_barras": "7701234567917", "etiquetas": ["pan", "francés", "fresco"],
            "ingredientes_receta": ["pan", "pan francés"],
        },
        {
            "id": "prod_029", "sku": "PAN-ARE-001", "nombre": "Arepa de Maíz",
            "descripcion": "Arepa de maíz blanco, paquete x10 unidades.",
            "descripcion_corta": "Arepa maíz x10",
            "categoria_id": "cat_010", "categoria_nombre": "Panadería",
            "marca": "Doña Arepa", "imagen_url": "/images/arepa.jpg",
            "precio_base": 5500, "precio_final": 5500, "tiene_promocion": False,
            "unidad_medida": "unidad", "contenido_neto": 10, "presentacion": "Paquete x10 unidades",
            "codigo_barras": "7701234567918", "etiquetas": ["arepa", "maíz", "desayuno"],
            "ingredientes_receta": ["arepa", "arepa de maíz"],
        },
    ]

    productos = {}
    for f in fixtures_data:
        producto = Producto(
            id=f["id"],
            sku=f["sku"],
            nombre=f["nombre"],
            descripcion=f.get("descripcion"),
            descripcion_corta=f.get("descripcion_corta"),
            categoria_id=f.get("categoria_id"),
            categoria_nombre=f.get("categoria_nombre"),
            marca=f.get("marca"),
            imagen_url=f.get("imagen_url"),
            precio_base=f["precio_base"],
            precio_final=f["precio_final"],
            tiene_promocion=f["tiene_promocion"],
            unidad_medida=f.get("unidad_medida"),
            contenido_neto=f.get("contenido_neto"),
            presentacion=f.get("presentacion"),
            codigo_barras=f.get("codigo_barras"),
            etiquetas=f.get("etiquetas", []),
            ingredientes_receta=f.get("ingredientes_receta", []),
            fuente="fixture_desarrollo",  # CRÍTICO: marca clara de datos ficticios
            fecha_actualizacion=datetime.now(),
        )
        productos[producto.id] = producto

    return productos


def crear_stock_fixture(productos: Dict[str, Producto]) -> Dict[str, Dict[str, int]]:
    """Crea stock aleatorio por sede para cada producto."""
    stock = {}
    for prod_id in productos.keys():
        stock[prod_id] = {
            MOCK_SEDE_UUID_1: random.randint(5, 100),
            MOCK_SEDE_UUID_2: random.randint(0, 80),
        }
    return stock


def crear_promociones_fixture() -> List[Promocion]:
    """Crea promociones de ejemplo."""
    from datetime import timedelta
    ahora = datetime.now()
    return [
        Promocion(
            id="promo_001",
            nombre="Descuento Frutas Tropicales",
            descripcion="20% descuento en mango, papaya y piña",
            tipo="descuento_porcentaje",
            valor=20.0,
            productos_ids=["prod_001"],
            categorias_ids=["cat_001"],
            fecha_inicio=ahora - timedelta(days=5),
            fecha_fin=ahora + timedelta(days=10),
            sede_ids=["sede_001", "sede_002"],
            activa=True,
        ),
        Promocion(
            id="promo_002",
            nombre="Leche 2x1",
            descripcion="Lleva 2 leches Alpina paga 1",
            tipo="lleva_x_paga_y",
            valor=2.0,
            productos_ids=["prod_011"],
            fecha_inicio=ahora - timedelta(days=2),
            fecha_fin=ahora + timedelta(days=5),
            sede_ids=["sede_001"],
            activa=True,
        ),
    ]


# Instancias globales (inicialización perezosa)
_PRODUCTOS_FIXTURE: Dict[str, Producto] = {}
_STOCK_FIXTURE: Dict[str, Dict[str, int]] = {}
_PROMOCIONES_FIXTURE: List[Promocion] = []


def obtener_productos_fixture() -> Dict[str, Producto]:
    """Retorna productos fixture (inicializa si necesario)."""
    global _PRODUCTOS_FIXTURE
    if not _PRODUCTOS_FIXTURE:
        _PRODUCTOS_FIXTURE = crear_productos_fixture()
    return _PRODUCTOS_FIXTURE


def obtener_stock_fixture() -> Dict[str, Dict[str, int]]:
    """Retorna stock fixture (inicializa si necesario)."""
    global _STOCK_FIXTURE
    if not _STOCK_FIXTURE:
        _STOCK_FIXTURE = crear_stock_fixture(obtener_productos_fixture())
    return _STOCK_FIXTURE


def obtener_promociones_fixture() -> List[Promocion]:
    """Retorna promociones fixture (inicializa si necesario)."""
    global _PROMOCIONES_FIXTURE
    if not _PROMOCIONES_FIXTURE:
        _PROMOCIONES_FIXTURE = crear_promociones_fixture()
    return _PROMOCIONES_FIXTURE