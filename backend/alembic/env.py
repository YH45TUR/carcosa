"""
Sistema Legal CO - Alembic Environment
Soporte para SQLite (dev) y PostgreSQL (prod) con auto-detección de modelos.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Agregar el directorio padre al path para importar modelos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Importar Base y todos los modelos para auto-detección
from app.db.database import Base

# Importar todos los modelos para auto-detección de Alembic
from app.models.user import User  # noqa
from app.models.case import Case, CaseDocument, CaseVersion, CaseTerm, TimelineEvent  # noqa

# Alembic Config object
config = context.config

# Interpretar archivo de configuración de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData objetivo para auto-migración
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecutar migraciones en modo 'offline' (solo genera SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecutar migraciones en modo 'online' (conectado a DB)."""
    # Soporte para DATABASE_URL de entorno (producción con PostgreSQL)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
