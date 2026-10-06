-- =====================================================================
-- Datos de prueba (seed) — Supermercado La Economía Aya
-- Se ejecuta después de init.sql en /docker-entrypoint-initdb.d
-- (orden alfabético). Usa UUIDs fijos para reproducibilidad.
-- =====================================================================

-- ------------------------- SEDES ---------------------------------------
INSERT INTO sedes (id, nombre, direccion) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Santa Isabel', 'Barrio Santa Isabel, Neiva, Huila'),
    ('a0000000-0000-0000-0000-000000000002', 'Machines',     'Barrio Machines, Neiva, Huila')
ON CONFLICT (id) DO NOTHING;

-- ------------------------- CATEGORÍAS -----------------------------------
INSERT INTO categorias (id, nombre, descripcion) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'Abarrotes', 'Productos básicos de despensa'),
    ('b0000000-0000-0000-0000-000000000002', 'Lácteos y huevos', 'Leche, huevos y derivados lácteos'),
    ('b0000000-0000-0000-0000-000000000003', 'Carnes', 'Carnes frías y proteína animal')
ON CONFLICT (id) DO NOTHING;

-- ------------------------- PRODUCTOS ------------------------------------
INSERT INTO productos (id, codigo_barras, nombre, descripcion, categoria_id, precio_venta, es_saludable, imagen_url) VALUES
    ('c0000000-0000-0000-0000-000000000001', '7702001001001', 'Arroz Diana x 500g',
     'Arroz blanco de grano largo, ideal para el consumo diario.',
     'b0000000-0000-0000-0000-000000000001', 3200.00, FALSE,
     'https://cdn.laeconomiaaya.co/img/arroz-diana-500g.jpg'),

    ('c0000000-0000-0000-0000-000000000002', '7702001002002', 'Leche entera Alqueria x 1L',
     'Leche entera pasteurizada, fuente de calcio y proteína.',
     'b0000000-0000-0000-0000-000000000002', 4500.00, TRUE,
     'https://cdn.laeconomiaaya.co/img/leche-alqueria-1l.jpg'),

    ('c0000000-0000-0000-0000-000000000003', '7702001003003', 'Aceite vegetal Gourmet x 500ml',
     'Aceite vegetal mixto apto para frituras y preparaciones diarias.',
     'b0000000-0000-0000-0000-000000000001', 6300.00, FALSE,
     'https://cdn.laeconomiaaya.co/img/aceite-gourmet-500ml.jpg'),

    ('c0000000-0000-0000-0000-000000000004', '7702001004004', 'Pechuga de pollo x 500g',
     'Pechuga de pollo fresca, alta en proteína y baja en grasa.',
     'b0000000-0000-0000-0000-000000000003', 9800.00, TRUE,
     'https://cdn.laeconomiaaya.co/img/pechuga-pollo-500g.jpg'),

    ('c0000000-0000-0000-0000-000000000005', '7702001005005', 'Huevos AA x 30 unidades',
     'Huevos rojos AA, cubeta de 30 unidades.',
     'b0000000-0000-0000-0000-000000000002', 15900.00, TRUE,
     'https://cdn.laeconomiaaya.co/img/huevos-aa-x30.jpg')
ON CONFLICT (id) DO NOTHING;

-- ------------------------- INVENTARIO POR SEDE --------------------------
-- Santa Isabel
INSERT INTO inventario_sedes (producto_id, sede_id, stock_actual, stock_minimo) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 34, 10),
    ('c0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 20, 8),
    ('c0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 15, 5),
    ('c0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 9,  5),
    ('c0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 12, 5)
ON CONFLICT (producto_id, sede_id) DO NOTHING;

-- Machines
INSERT INTO inventario_sedes (producto_id, sede_id, stock_actual, stock_minimo) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002', 12, 10),
    ('c0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000002', 6,  8),
    ('c0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000002', 0,  5),
    ('c0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000002', 18, 5),
    ('c0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000002', 7,  5)
ON CONFLICT (producto_id, sede_id) DO NOTHING;

-- ------------------------- COLA DE SIIGO (registro de prueba) -----------
INSERT INTO transacciones_siigo (sede_id, payload_json, estado, intentos) VALUES
    ('a0000000-0000-0000-0000-000000000002',
     '{
        "evento": "actualizacion_inventario",
        "codigo_siigo_sede": "Machines",
        "productos": [
          { "codigo_barras": "7702001003003", "stock": 0, "precio": 6300.00 }
        ]
      }'::jsonb,
     'PENDIENTE', 0)
ON CONFLICT DO NOTHING;

-- Nota: embeddings_productos se deja vacía intencionalmente; se puebla
-- mediante el script de ingesta (app/services/embeddings.py) que llama
-- al proveedor de embeddings configurado sobre el catálogo real.
