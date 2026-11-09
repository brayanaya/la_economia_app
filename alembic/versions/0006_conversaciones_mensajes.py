"""Agregar tablas de conversaciones y mensajes con pgvector

Revision ID: 0006
Revises: 0005
Create Date: 2025-10-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Asegurar usuario invitado para conversaciones públicas/anónimas
    op.execute("""
        INSERT INTO customers (id, email, nombre, consentimiento_datos)
        VALUES ('00000000-0000-0000-0000-000000000000', 'invitado@laeconomiaaya.internal', 'Invitado General', true)
        ON CONFLICT (id) DO NOTHING;
    """)

    # Crear tipo enum para tipo_remitente
    op.execute("CREATE TYPE tipo_remitente_enum AS ENUM ('usuario', 'asistente', 'sistema')")

    # Tabla conversaciones
    op.create_table(
        'conversaciones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('productos_recientes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('receta_actual', postgresql.JSONB(), nullable=True),
        sa.Column('lista_mercado', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('presupuesto', postgresql.JSONB(), nullable=True),
        sa.Column('resumen', sa.Text(), nullable=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['usuario_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversaciones_usuario_actualizado', 'conversaciones', ['usuario_id', 'actualizado_en'], unique=False)

    # Tabla mensajes
    op.create_table(
        'mensajes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversacion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('remitente', sa.Enum('usuario', 'asistente', 'sistema', name='tipo_remitente_enum', create_type=False), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),  # pgvector se maneja como array en SQLAlchemy básico
        sa.Column('tokens_entrada', sa.Integer(), nullable=True),
        sa.Column('tokens_salida', sa.Integer(), nullable=True),
        sa.Column('modelo_usado', sa.String(length=100), nullable=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversacion_id'], ['conversaciones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mensajes_conversacion_creado', 'mensajes', ['conversacion_id', 'creado_en'], unique=False)

    # Nota: El índice vectorial (ivfflat) se debe crear manualmente después de poblar datos
    # CREATE INDEX ix_mensajes_embedding ON mensajes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


def downgrade() -> None:
    op.drop_index('ix_mensajes_conversacion_creado', table_name='mensajes')
    op.drop_table('mensajes')
    op.drop_index('ix_conversaciones_usuario_actualizado', table_name='conversaciones')
    op.drop_table('conversaciones')
    op.execute("DROP TYPE tipo_remitente_enum")