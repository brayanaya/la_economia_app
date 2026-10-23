"""customer accounts and revocable sessions

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("customers", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("email", sa.String(254), nullable=False), sa.Column("nombre", sa.String(120), nullable=False), sa.Column("password_hash", sa.String(512), nullable=False))
    op.create_index("ix_customers_email", "customers", ["email"], unique=True)
    op.create_table("customer_sessions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("csrf_token", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_customer_sessions_user_id", "customer_sessions", ["user_id"]); op.create_index("ix_customer_sessions_token_hash", "customer_sessions", ["token_hash"], unique=True); op.create_index("ix_customer_sessions_expires_at", "customer_sessions", ["expires_at"])
    op.add_column("ordenes", sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True)); op.create_foreign_key("fk_ordenes_customer_id_customers", "ordenes", "customers", ["customer_id"], ["id"], ondelete="SET NULL"); op.create_index("ix_ordenes_customer_id", "ordenes", ["customer_id"])
def downgrade():
    op.drop_index("ix_ordenes_customer_id", table_name="ordenes"); op.drop_constraint("fk_ordenes_customer_id_customers", "ordenes", type_="foreignkey"); op.drop_column("ordenes", "customer_id")
    op.drop_index("ix_customer_sessions_expires_at", table_name="customer_sessions"); op.drop_index("ix_customer_sessions_token_hash", table_name="customer_sessions"); op.drop_index("ix_customer_sessions_user_id", table_name="customer_sessions"); op.drop_table("customer_sessions"); op.drop_index("ix_customers_email", table_name="customers"); op.drop_table("customers")
