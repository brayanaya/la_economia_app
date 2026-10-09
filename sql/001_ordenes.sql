-- carrito-v1 : modulo ordenes (idempotente)
CREATE TABLE IF NOT EXISTS ordenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sede_id UUID NOT NULL,
    cliente_nombre VARCHAR(120) NOT NULL,
    cliente_telefono VARCHAR(30),
    notas VARCHAR(500),
    total NUMERIC(12,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ordenes_sede_id ON ordenes (sede_id);

CREATE TABLE IF NOT EXISTS detalles_orden (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orden_id UUID NOT NULL REFERENCES ordenes(id) ON DELETE CASCADE,
    producto_id VARCHAR(64) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    imagen_url VARCHAR(500),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0),
    subtotal NUMERIC(12,2) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_detalles_orden_orden_id ON detalles_orden (orden_id);

DO $$
BEGIN
    IF to_regclass('public.sedes') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_ordenes_sede') THEN
        BEGIN
            ALTER TABLE ordenes ADD CONSTRAINT fk_ordenes_sede FOREIGN KEY (sede_id) REFERENCES sedes(id);
        EXCEPTION WHEN others THEN
            RAISE NOTICE 'FK a sedes omitida: %', SQLERRM;
        END;
    END IF;
END $$;