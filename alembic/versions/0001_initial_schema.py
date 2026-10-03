"""esquema inicial: sedes, categorias, productos, inventario_sedes,
embeddings_productos, transacciones_siigo

Revision ID: 0001
Revises:
Create Date: 2026-09-19

Nota: esta migración baseline replica exactamente el esquema definido en
db/init.sql, de manera que un entorno provisto mediante Docker (que ya
ejecutó init.sql en la inicialización del volumen) y un entorno gestionado
mediante `alembic upgrade head` converjan al mismo estado de esquema.
"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "sedes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("nombre", sa.String(100), nullable=False, unique=True),
        sa.Column("direccion", sa.String(255)),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "categorias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("nombre", sa.String(100), nullable=False, unique=True),
        sa.Column("descripcion", sa.Text()),
    )

    op.create_table(
        "productos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("codigo_barras", sa.String(50), nullable=False, unique=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("categoria_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("precio_venta", sa.Numeric(12, 2), nullable=False),
        sa.Column("es_saludable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("imagen_url", sa.Text()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("precio_venta >= 0", name="ck_precio_venta_no_negativo"),
    )

    op.create_table(
        "inventario_sedes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("producto_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("productos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sedes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_actual", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stock_minimo", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ultima_actualizacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("producto_id", "sede_id", name="uq_producto_sede"),
        sa.CheckConstraint("stock_actual >= 0", name="ck_stock_actual_no_negativo"),
        sa.CheckConstraint("stock_minimo >= 0", name="ck_stock_minimo_no_negativo"),
    )

    op.create_table(
        "embeddings_productos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("producto_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("productos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contenido_textual", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(768), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "transacciones_siigo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_log", sa.Text()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("procesado_en", sa.DateTime(timezone=True)),
        sa.CheckConstraint("estado IN ('PENDIENTE','PROCESADO','ERROR')", name="ck_estado_siigo_valido"),
    )

    op.create_index(
        "idx_embeddings_hnsw", "embeddings_productos", ["embedding"],
        postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index("idx_inventario_producto_id", "inventario_sedes", ["producto_id"])
    op.create_index("idx_inventario_sede_id", "inventario_sedes", ["sede_id"])
    op.create_index("idx_siigo_estado", "transacciones_siigo", ["estado"])
    op.create_index("idx_siigo_sede_id", "transacciones_siigo", ["sede_id"])
    op.create_index("idx_embeddings_producto_id", "embeddings_productos", ["producto_id"])

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_touch_ultima_actualizacion()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.ultima_actualizacion := now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_inventario_touch
            BEFORE UPDATE ON inventario_sedes
            FOR EACH ROW
            EXECUTE FUNCTION fn_touch_ultima_actualizacion();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_inventario_touch ON inventario_sedes")
    op.execute("DROP FUNCTION IF EXISTS fn_touch_ultima_actualizacion")
    op.drop_table("transacciones_siigo")
    op.drop_table("embeddings_productos")
    op.drop_table("inventario_sedes")
    op.drop_table("productos")
    op.drop_table("categorias")
    op.drop_table("sedes")
