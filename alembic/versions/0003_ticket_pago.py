"""Persistir un identificador aleatorio para cada ticket de pago."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

revision = "0003_ticket_pago"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tablas = set(inspect(bind).get_table_names())

    if "ordenes" not in tablas:
        op.create_table(
            "ordenes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("cliente_nombre", sa.String(120), nullable=False),
            sa.Column("cliente_telefono", sa.String(30), nullable=True),
            sa.Column("notas", sa.String(500), nullable=True),
            sa.Column("total", sa.Numeric(12, 2), nullable=False),
            sa.Column("estado", sa.String(20), nullable=False,
                      server_default="pendiente"),
            sa.Column("creado_en", sa.DateTime(timezone=True),
                      nullable=False, server_default=sa.func.now()),
        )

    tablas = set(inspect(bind).get_table_names())
    if "detalles_orden" not in tablas:
        op.create_table(
            "detalles_orden",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("orden_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("ordenes.id", ondelete="CASCADE"),
                      nullable=False),
            sa.Column("producto_id", sa.String(64), nullable=False),
            sa.Column("nombre", sa.String(200), nullable=False),
            sa.Column("imagen_url", sa.String(500), nullable=True),
            sa.Column("cantidad", sa.Integer(), nullable=False),
            sa.Column("precio_unitario", sa.Numeric(12, 2), nullable=False),
            sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        )
        op.create_index("ix_detalles_orden_orden_id", "detalles_orden", ["orden_id"])

    columnas = {columna["name"] for columna in inspect(bind).get_columns("ordenes")}
    if "ticket_id" not in columnas:
        op.add_column(
            "ordenes",
            sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

    op.execute(
        "UPDATE ordenes SET ticket_id = gen_random_uuid() WHERE ticket_id IS NULL"
    )
    op.alter_column(
        "ordenes",
        "ticket_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )

    indices = {indice["name"] for indice in inspect(bind).get_indexes("ordenes")}
    if "uq_ordenes_ticket_id" not in indices:
        op.create_index(
            "uq_ordenes_ticket_id",
            "ordenes",
            ["ticket_id"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    tablas = set(inspect(bind).get_table_names())
    if "ordenes" not in tablas:
        return

    indices = {indice["name"] for indice in inspect(bind).get_indexes("ordenes")}
    if "uq_ordenes_ticket_id" in indices:
        op.drop_index("uq_ordenes_ticket_id", table_name="ordenes")

    columnas = {columna["name"] for columna in inspect(bind).get_columns("ordenes")}
    if "ticket_id" in columnas:
        op.drop_column("ordenes", "ticket_id")
