-- =====================================================================
-- Supermercado La Economía Aya — Esquema de base de datos
-- PostgreSQL 16 + pgvector
-- Sedes: Santa Isabel (2019) y Machines (2020) — Neiva, Huila
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================================
-- Tabla: sedes
-- =====================================================================
CREATE TABLE IF NOT EXISTS sedes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    direccion   VARCHAR(255),
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- Tabla: categorias
-- =====================================================================
CREATE TABLE IF NOT EXISTS categorias (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre       VARCHAR(100) NOT NULL UNIQUE,
    descripcion  TEXT
);

-- =====================================================================
-- Tabla: productos
-- =====================================================================
CREATE TABLE IF NOT EXISTS productos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_barras   VARCHAR(50) NOT NULL UNIQUE,
    nombre          VARCHAR(200) NOT NULL,
    descripcion     TEXT,
    categoria_id    UUID NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
    precio_venta    NUMERIC(12,2) NOT NULL CHECK (precio_venta >= 0),
    es_saludable    BOOLEAN NOT NULL DEFAULT FALSE,
    imagen_url      TEXT,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- Tabla: inventario_sedes (relación M:N productos <-> sedes)
-- =====================================================================
CREATE TABLE IF NOT EXISTS inventario_sedes (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id           UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    sede_id               UUID NOT NULL REFERENCES sedes(id) ON DELETE CASCADE,
    stock_actual          INTEGER NOT NULL DEFAULT 0 CHECK (stock_actual >= 0),
    stock_minimo          INTEGER NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),
    ultima_actualizacion  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_producto_sede UNIQUE (producto_id, sede_id)
);

CREATE OR REPLACE FUNCTION fn_touch_ultima_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultima_actualizacion := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_inventario_touch ON inventario_sedes;
CREATE TRIGGER trg_inventario_touch
    BEFORE UPDATE ON inventario_sedes
    FOR EACH ROW
    EXECUTE FUNCTION fn_touch_ultima_actualizacion();

-- =====================================================================
-- Tabla: embeddings_productos (soporte RAG)
-- vector(768): compatible con Sentence-Transformers multilingüe nativo
-- y con OpenAI text-embedding-3-small invocado con dimensions=768
-- =====================================================================
CREATE TABLE IF NOT EXISTS embeddings_productos (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id        UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    contenido_textual  TEXT NOT NULL,
    embedding          VECTOR(768) NOT NULL,
    creado_en          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- Tabla: transacciones_siigo (cola de sincronización con el POS Siigo)
-- =====================================================================
CREATE TABLE IF NOT EXISTS transacciones_siigo (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sede_id        UUID NOT NULL REFERENCES sedes(id) ON DELETE RESTRICT,
    payload_json   JSONB NOT NULL,
    estado         VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE'
                   CHECK (estado IN ('PENDIENTE', 'PROCESADO', 'ERROR')),
    intentos       INTEGER NOT NULL DEFAULT 0,
    error_log      TEXT,
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    procesado_en   TIMESTAMPTZ
);

-- =====================================================================
-- ÍNDICES DE RENDIMIENTO
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
    ON embeddings_productos
    USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_inventario_producto_id ON inventario_sedes (producto_id);
CREATE INDEX IF NOT EXISTS idx_inventario_sede_id     ON inventario_sedes (sede_id);
CREATE INDEX IF NOT EXISTS idx_siigo_estado           ON transacciones_siigo (estado);
CREATE INDEX IF NOT EXISTS idx_siigo_sede_id          ON transacciones_siigo (sede_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_producto_id ON embeddings_productos (producto_id);
-- codigo_barras ya cuenta con índice único implícito (UNIQUE constraint).
