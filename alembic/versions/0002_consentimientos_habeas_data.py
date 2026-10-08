"""consentimientos_habeas_data

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consentimientos_habeas_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("ip_origen", sa.String(length=45), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("acepto_politica", sa.Boolean(), nullable=False),
        sa.Column("acepto_cookies", sa.Boolean(), nullable=False),
        sa.Column("version_politica", sa.String(length=32), nullable=False),
        sa.Column("fecha_registro", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("consentimientos_habeas_data")