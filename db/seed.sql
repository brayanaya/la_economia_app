-- =====================================================================
-- Datos de prueba (seed) — Supermercado La Economía Aya
-- Se ejecuta después de init.sql en /docker-entrypoint-initdb.d
-- (orden alfabético). Usa UUIDs fijos para reproducibilidad.
--
-- Idempotente: cada bloque hace ON CONFLICT ... DO UPDATE, así que se
-- puede re-ejecutar sobre una base existente para refrescar catálogo,
-- precios, imágenes e inventario. Para regenerar los embeddings usa
-- `python -m scripts.seed_catalogo` (requiere el proveedor de
-- embeddings activo: Ollama, OpenAI o sentence-transformers).
-- =====================================================================

-- ------------------------- SEDES ---------------------------------------
INSERT INTO sedes (id, nombre, direccion) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Santa Isabel', 'Calle 10 Sur 21-92, Neiva, Huila'),
    ('a0000000-0000-0000-0000-000000000002', 'Machines',     'Cra. 52 #26A-13, Neiva, Huila')
ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre, direccion = EXCLUDED.direccion;

-- ------------------------- CATEGORÍAS -----------------------------------
INSERT INTO categorias (id, nombre, descripcion) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'Granos y abarrotes', 'Arroz, fríjol, lentejas, aceites y básicos de despensa'),
    ('b0000000-0000-0000-0000-000000000002', 'Lácteos y huevos',  'Leche, huevos, quesos, yogures y derivados lácteos'),
    ('b0000000-0000-0000-0000-000000000003', 'Cárnicos',           'Carnes frescas, pollo y carnes frías'),
    ('b0000000-0000-0000-0000-000000000004', 'Frutas y verduras',  'Fruver: hortalizas, tubérculos, frutas y verduras frescas'),
    ('b0000000-0000-0000-0000-000000000005', 'Panadería',          'Panes, arepas y productos de panadería'),
    ('b0000000-0000-0000-0000-000000000006', 'Despensa',           'Café, chocolate, panela, avena, sal y enlatados'),
    ('b0000000-0000-0000-0000-000000000007', 'Bebidas',           'Gaseosas, jugos, agua y bebidas frías'),
    ('b0000000-0000-0000-0000-000000000008', 'Aseo y hogar',      'Detergentes y productos de limpieza'),
    ('b0000000-0000-0000-0000-000000000009', 'Cuidado personal',   'Jabones, shampoo e higiene personal'),
    ('b0000000-0000-0000-0000-000000000010', 'Licores',            'Cervezas y bebidas alcohólicas')
ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre, descripcion = EXCLUDED.descripcion;

-- ------------------------- PRODUCTOS ------------------------------------
-- Las imágenes viven en frontend/public/img/productos y se sirven desde el
-- propio frontend; imagen_url guarda la ruta relativa.
INSERT INTO productos (id, codigo_barras, nombre, descripcion, categoria_id, precio_venta, es_saludable, imagen_url) VALUES
    ('c0000000-0000-0000-0000-000000000001', '7702001001001', 'Arroz blanco Diana x 500g',
     'Arroz blanco de grano suelto. Base de la canasta familiar colombiana: ideal para el calentado, acompañamientos y almuerzos diarios.',
     'b0000000-0000-0000-0000-000000000001', 3900.00, FALSE, '/img/productos/arroz.svg'),

    ('c0000000-0000-0000-0000-000000000002', '7702001002002', 'Leche entera Alquería x 1L',
     'Leche entera pasteurizada, fuente de calcio y proteína. Perfecta para el desayuno con chocolate, café o avena.',
     'b0000000-0000-0000-0000-000000000002', 4900.00, TRUE, '/img/productos/leche.svg'),

    ('c0000000-0000-0000-0000-000000000003', '7702001003003', 'Aceite vegetal Gourmet x 500ml',
     'Aceite vegetal mixto apto para frituras, guisos y preparaciones diarias de la cocina.',
     'b0000000-0000-0000-0000-000000000001', 7400.00, FALSE, '/img/productos/aceite.svg'),

    ('c0000000-0000-0000-0000-000000000004', '7702001004004', 'Pechuga de pollo fresca x 500g',
     'Pechuga de pollo fresca, alta en proteína y baja en grasa. Ideal para almuerzos y preparaciones a la plancha.',
     'b0000000-0000-0000-0000-000000000003', 13400.00, TRUE, '/img/productos/pollo.svg'),

    ('c0000000-0000-0000-0000-000000000005', '7702001005005', 'Huevos AA rojos x 30 unidades',
     'Cubeta de 30 huevos rojos AA, frescos de la región. Los infaltables del desayuno: pericos, revueltos o tibios.',
     'b0000000-0000-0000-0000-000000000002', 16900.00, TRUE, '/img/productos/huevos.svg'),

    ('c0000000-0000-0000-0000-000000000006', '7702001006006', 'Fríjol cargamanto x 500g',
     'Fríjol cargamanto santafereño, la base del calentado paisa y de las sopas de la abuela.',
     'b0000000-0000-0000-0000-000000000001', 5600.00, TRUE, '/img/productos/frijol.svg'),

    ('c0000000-0000-0000-0000-000000000007', '7702001007007', 'Lentejas conchas x 500g',
     'Lentejas conchas de grano entero, ricas en hierro y fibra. Clásicas en sopas y guisos caseros.',
     'b0000000-0000-0000-0000-000000000001', 4900.00, TRUE, '/img/productos/lentejas.svg'),

    ('c0000000-0000-0000-0000-000000000008', '7702001008008', 'Arepa blanca x 6 unidades',
     'Arepa blanca asadera, paquete de 6 unidades. La compañera del desayuno con queso, mantequilla o huevos pericos.',
     'b0000000-0000-0000-0000-000000000005', 5900.00, TRUE, '/img/productos/arepa.svg'),

    ('c0000000-0000-0000-0000-000000000009', '7702001009009', 'Pan tajado blanco x 400g',
     'Pan tajado blanco, suave y fresco. Ideal para el desayuno con mantequilla, queso o jamón.',
     'b0000000-0000-0000-0000-000000000005', 4300.00, FALSE, '/img/productos/pan.svg'),

    ('c0000000-0000-0000-0000-000000000010', '7702001010010', 'Chocolate en polvo x 250g',
     'Chocolate en polvo para preparar el chocolate caliente de la tarde o el desayuno con queso y almojábana.',
     'b0000000-0000-0000-0000-000000000006', 9800.00, FALSE, '/img/productos/chocolate.svg'),

    ('c0000000-0000-0000-0000-000000000011', '7702001011011', 'Queso campesino x 500g',
     'Queso campesino fresco, ideal para el desayuno con arepa, para el chocolate caliente o para tostar en sartén.',
     'b0000000-0000-0000-0000-000000000002', 12500.00, TRUE, '/img/productos/queso.svg'),

    ('c0000000-0000-0000-0000-000000000012', '7702001012012', 'Tomate chonto x 500g',
     'Tomate chonto maduro, la base del hogao y de los huevos pericos. Fresco y de la región.',
     'b0000000-0000-0000-0000-000000000004', 2900.00, TRUE, '/img/productos/tomate.svg'),

    ('c0000000-0000-0000-0000-000000000013', '7702001013013', 'Cebolla larga junca x 500g',
     'Cebolla larga junca fresca, infaltable en el hogao, los pericos y los guisos colombianos.',
     'b0000000-0000-0000-0000-000000000004', 2500.00, TRUE, '/img/productos/cebolla-larga.svg'),

    ('c0000000-0000-0000-0000-000000000014', '7702001014014', 'Sal refinada x 500g',
     'Sal refinada de cocina, para sazonar pericos, sopas y preparaciones del día a día.',
     'b0000000-0000-0000-0000-000000000006', 1900.00, FALSE, '/img/productos/sal.svg'),

    ('c0000000-0000-0000-0000-000000000015', '7702001015015', 'Café tostado molido x 250g',
     'Café tostado molido de origen colombiano. El aromático que abre el desayuno y acompaña las tardes.',
     'b0000000-0000-0000-0000-000000000006', 12900.00, FALSE, '/img/productos/cafe.svg'),

    ('c0000000-0000-0000-0000-000000000016', '7702001016016', 'Panela redonda x 500g',
     'Panela redonda de caña, para el agua de panela caliente con queso o limón. Tradición campesina.',
     'b0000000-0000-0000-0000-000000000006', 3800.00, TRUE, '/img/productos/panela.svg'),

    ('c0000000-0000-0000-0000-000000000017', '7702001017017', 'Plátano hartón x kilo',
     'Plátano hartón fresco, para patacones, cocidos o madurados. Fruta de la región.',
     'b0000000-0000-0000-0000-000000000004', 3200.00, TRUE, '/img/productos/platano.svg'),

    ('c0000000-0000-0000-0000-000000000018', '7702001018018', 'Papa criolla x kilo',
     'Papa criolla amarilla, ideal para el calentado, purés y sopas. La papa sabrosa de siempre.',
     'b0000000-0000-0000-0000-000000000004', 4900.00, TRUE, '/img/productos/papa.svg'),

    ('c0000000-0000-0000-0000-000000000019', '7702001019019', 'Yuca fresca x kilo',
     'Yuca fresca de la región, para frita, cocida o en sancocho. Compañera del calentado.',
     'b0000000-0000-0000-0000-000000000004', 3500.00, TRUE, '/img/productos/yuca.svg'),

    ('c0000000-0000-0000-0000-000000000020', '7702001020020', 'Aguacate hass x 500g',
     'Aguacate hass cremoso, para guacamole, ensaladas o la tajada de las tardes.',
     'b0000000-0000-0000-0000-000000000004', 6500.00, TRUE, '/img/productos/aguacate.svg'),

    ('c0000000-0000-0000-0000-000000000021', '7702001021021', 'Jamón de cerro x 250g',
     'Jamón de cerro en láminas, ideal para sánduches, arepas o el desayuno con pan.',
     'b0000000-0000-0000-0000-000000000003', 10900.00, FALSE, '/img/productos/jamon.svg'),

    ('c0000000-0000-0000-0000-000000000022', '7702001022022', 'Avena en hojuelas x 250g',
     'Avena en hojuelas, desayuno saludable con leche, frutas o en avena caliente con panela.',
     'b0000000-0000-0000-0000-000000000006', 4200.00, TRUE, '/img/productos/avena.svg'),

    ('c0000000-0000-0000-0000-000000000023', '7702001023023', 'Yogur natural fresa x 1L',
     'Yogur natural con fresa, fuente de calcio. Desayuno o merienda con granola o avena.',
     'b0000000-0000-0000-0000-000000000002', 8900.00, TRUE, '/img/productos/yogur.svg'),

    ('c0000000-0000-0000-0000-000000000024', '7702001024024', 'Gaseosa cola x 1.5L',
     'Gaseosa tipo cola familiar de 1.5 litros, bien fría para el almuerzo.',
     'b0000000-0000-0000-0000-000000000007', 4700.00, FALSE, '/img/productos/gaseosa.svg'),

    ('c0000000-0000-0000-0000-000000000025', '7702001025025', 'Cerveza Águila x 6 unidades',
     'Sixpack de cerveza Águila, la preferida para el partido y el asado. Venta prohibida a menores de edad.',
     'b0000000-0000-0000-0000-000000000010', 16900.00, FALSE, '/img/productos/cerveza.svg'),

    ('c0000000-0000-0000-0000-000000000026', '7702001026026', 'Detergente en polvo x 500g',
     'Detergente en polvo de alto rendimiento para ropa blanca y de color.',
     'b0000000-0000-0000-0000-000000000008', 6200.00, FALSE, '/img/productos/detergente.svg'),

    ('c0000000-0000-0000-0000-000000000027', '7702001027027', 'Jabón de baño x 110g',
     'Jabón de baño humectante para el cuidado diario de la piel.',
     'b0000000-0000-0000-0000-000000000009', 2800.00, FALSE, '/img/productos/jabon.svg')
ON CONFLICT (id) DO UPDATE SET
    codigo_barras = EXCLUDED.codigo_barras,
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    categoria_id = EXCLUDED.categoria_id,
    precio_venta = EXCLUDED.precio_venta,
    es_saludable = EXCLUDED.es_saludable,
    imagen_url = EXCLUDED.imagen_url;

-- ------------------------- INVENTARIO POR SEDE --------------------------
-- Santa Isabel (a...01)
INSERT INTO inventario_sedes (producto_id, sede_id, stock_actual, stock_minimo) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 40, 10),
    ('c0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 24, 8),
    ('c0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 18, 5),
    ('c0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 12, 5),
    ('c0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 15, 5),
    ('c0000000-0000-0000-0000-000000000006', 'a0000000-0000-0000-0000-000000000001', 30, 8),
    ('c0000000-0000-0000-0000-000000000007', 'a0000000-0000-0000-0000-000000000001', 26, 8),
    ('c0000000-0000-0000-0000-000000000008', 'a0000000-0000-0000-0000-000000000001', 22, 6),
    ('c0000000-0000-0000-0000-000000000009', 'a0000000-0000-0000-0000-000000000001', 20, 6),
    ('c0000000-0000-0000-0000-000000000010', 'a0000000-0000-0000-0000-000000000001', 16, 5),
    ('c0000000-0000-0000-0000-000000000011', 'a0000000-0000-0000-0000-000000000001', 14, 5),
    ('c0000000-0000-0000-0000-000000000012', 'a0000000-0000-0000-0000-000000000001', 28, 8),
    ('c0000000-0000-0000-0000-000000000013', 'a0000000-0000-0000-0000-000000000001', 25, 8),
    ('c0000000-0000-0000-0000-000000000014', 'a0000000-0000-0000-0000-000000000001', 35, 10),
    ('c0000000-0000-0000-0000-000000000015', 'a0000000-0000-0000-0000-000000000001', 20, 6),
    ('c0000000-0000-0000-0000-000000000016', 'a0000000-0000-0000-0000-000000000001', 32, 8),
    ('c0000000-0000-0000-0000-000000000017', 'a0000000-0000-0000-0000-000000000001', 24, 8),
    ('c0000000-0000-0000-0000-000000000018', 'a0000000-0000-0000-0000-000000000001', 30, 8),
    ('c0000000-0000-0000-0000-000000000019', 'a0000000-0000-0000-0000-000000000001', 26, 8),
    ('c0000000-0000-0000-0000-000000000020', 'a0000000-0000-0000-0000-000000000001', 0,  4),
    ('c0000000-0000-0000-0000-000000000021', 'a0000000-0000-0000-0000-000000000001', 10, 4),
    ('c0000000-0000-0000-0000-000000000022', 'a0000000-0000-0000-0000-000000000001', 18, 6),
    ('c0000000-0000-0000-0000-000000000023', 'a0000000-0000-0000-0000-000000000001', 12, 4),
    ('c0000000-0000-0000-0000-000000000024', 'a0000000-0000-0000-0000-000000000001', 22, 6),
    ('c0000000-0000-0000-0000-000000000025', 'a0000000-0000-0000-0000-000000000001', 8,  4),
    ('c0000000-0000-0000-0000-000000000026', 'a0000000-0000-0000-0000-000000000001', 16, 5),
    ('c0000000-0000-0000-0000-000000000027', 'a0000000-0000-0000-0000-000000000001', 30, 8)
ON CONFLICT (producto_id, sede_id) DO UPDATE SET
    stock_actual = EXCLUDED.stock_actual,
    stock_minimo = EXCLUDED.stock_minimo;

-- Machines (a...02) — nombre comercial de la sede: "Palmas"
INSERT INTO inventario_sedes (producto_id, sede_id, stock_actual, stock_minimo) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002', 20, 10),
    ('c0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000002', 10, 8),
    ('c0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000002', 0,  5),
    ('c0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000002', 16, 5),
    ('c0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000002', 9,  5),
    ('c0000000-0000-0000-0000-000000000006', 'a0000000-0000-0000-0000-000000000002', 14, 8),
    ('c0000000-0000-0000-0000-000000000007', 'a0000000-0000-0000-0000-000000000002', 12, 8),
    ('c0000000-0000-0000-0000-000000000008', 'a0000000-0000-0000-0000-000000000002', 15, 6),
    ('c0000000-0000-0000-0000-000000000009', 'a0000000-0000-0000-0000-000000000002', 13, 6),
    ('c0000000-0000-0000-0000-000000000010', 'a0000000-0000-0000-0000-000000000002', 11, 5),
    ('c0000000-0000-0000-0000-000000000011', 'a0000000-0000-0000-0000-000000000002', 8,  4),
    ('c0000000-0000-0000-0000-000000000012', 'a0000000-0000-0000-0000-000000000002', 18, 8),
    ('c0000000-0000-0000-0000-000000000013', 'a0000000-0000-0000-0000-000000000002', 20, 8),
    ('c0000000-0000-0000-0000-000000000014', 'a0000000-0000-0000-0000-000000000002', 24, 10),
    ('c0000000-0000-0000-0000-000000000015', 'a0000000-0000-0000-0000-000000000002', 9,  4),
    ('c0000000-0000-0000-0000-000000000016', 'a0000000-0000-0000-0000-000000000002', 17, 6),
    ('c0000000-0000-0000-0000-000000000017', 'a0000000-0000-0000-0000-000000000002', 15, 6),
    ('c0000000-0000-0000-0000-000000000018', 'a0000000-0000-0000-0000-000000000002', 21, 8),
    ('c0000000-0000-0000-0000-000000000019', 'a0000000-0000-0000-0000-000000000002', 19, 6),
    ('c0000000-0000-0000-0000-000000000020', 'a0000000-0000-0000-0000-000000000002', 6,  4),
    ('c0000000-0000-0000-0000-000000000021', 'a0000000-0000-0000-0000-000000000002', 7,  4),
    ('c0000000-0000-0000-0000-000000000022', 'a0000000-0000-0000-0000-000000000002', 10, 4),
    ('c0000000-0000-0000-0000-000000000023', 'a0000000-0000-0000-0000-000000000002', 6,  4),
    ('c0000000-0000-0000-0000-000000000024', 'a0000000-0000-0000-0000-000000000002', 14, 6),
    ('c0000000-0000-0000-0000-000000000026', 'a0000000-0000-0000-0000-000000000002', 12, 5),
    ('c0000000-0000-0000-0000-000000000027', 'a0000000-0000-0000-0000-000000000002', 18, 8)
ON CONFLICT (producto_id, sede_id) DO UPDATE SET
    stock_actual = EXCLUDED.stock_actual,
    stock_minimo = EXCLUDED.stock_minimo;
-- Nota: la cerveza (c...25) no se vende en la sede Machines/Palmas.

-- ------------------------- COLA DE SIIGO (registro de prueba) -----------
INSERT INTO transacciones_siigo (sede_id, payload_json, estado, intentos) VALUES
    ('a0000000-0000-0000-0000-000000000002',
     '{
        "evento": "actualizacion_inventario",
        "codigo_siigo_sede": "Machines",
        "productos": [
          { "codigo_barras": "7702001003003", "stock": 0, "precio": 7400.00 }
        ]
      }'::jsonb,
     'PENDIENTE', 0)
ON CONFLICT DO NOTHING;

-- Nota: embeddings_productos se deja vacía intencionalmente; se puebla
-- con `python -m scripts.seed_catalogo` (o el script de ingesta), que llama
-- al proveedor de embeddings configurado sobre el catálogo real.
