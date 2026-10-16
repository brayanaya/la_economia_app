ALTER TABLE inventario_sedes ADD COLUMN IF NOT EXISTS stock_reservado INTEGER NOT NULL DEFAULT 0;
ALTER TABLE inventario_sedes DROP CONSTRAINT IF EXISTS ck_stock_reserv_no_negativo;
ALTER TABLE inventario_sedes ADD CONSTRAINT ck_stock_reserv_no_negativo CHECK (stock_reservado >= 0);
ALTER TABLE inventario_sedes DROP CONSTRAINT IF EXISTS ck_stock_coherente;
ALTER TABLE inventario_sedes ADD CONSTRAINT ck_stock_coherente CHECK (stock_actual >= stock_reservado);
