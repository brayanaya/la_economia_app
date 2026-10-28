"""pagos en linea (wompi) y metodo de pago de la orden

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("ordenes", sa.Column("metodo_pago", sa.String(30), nullable=True))
    op.create_table("pagos", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("orden_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False), sa.Column("proveedor", sa.String(30), nullable=False, server_default="wompi"), sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"), sa.Column("referencia", sa.String(64), nullable=False), sa.Column("monto_centavos", sa.Integer, nullable=False), sa.Column("moneda", sa.String(3), nullable=False, server_default="COP"), sa.Column("transaccion_id", sa.String(64), nullable=True), sa.Column("metadatos", sa.JSON, nullable=True), sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_pagos_orden_id", "pagos", ["orden_id"]); op.create_index("ix_pagos_referencia", "pagos", ["referencia"], unique=True); op.create_index("ix_pagos_transaccion_id", "pagos", ["transaccion_id"]); op.create_index("ix_pagos_estado", "pagos", ["estado"])
def downgrade():
    op.drop_index("ix_pagos_estado", table_name="pagos"); op.drop_index("ix_pagos_transaccion_id", table_name="pagos"); op.drop_index("ix_pagos_referencia", table_name="pagos"); op.drop_index("ix_pagos_orden_id", table_name="pagos"); op.drop_table("pagos")
    op.drop_column("ordenes", "metodo_pago")
