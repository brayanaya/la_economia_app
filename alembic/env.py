import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='ignore')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='ignore')

from alembic import context
from logging.config import fileConfig
import logging

# Asegurar que el directorio raiz del proyecto esta en sys.path
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings

config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Inyectar la URL sincrona de la base de datos desde la configuracion
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

def run_migrations_online():
    from sqlalchemy import create_engine
    connectable = create_engine(settings.database_url_sync)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    pass
else:
    run_migrations_online()