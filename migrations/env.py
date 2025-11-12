"""
Alembic Migration Environment
Handles migrations for both main database and audit database
Reference: docs/06-data_schema.md, docs/10-audit_architecture.md
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings
from src.core.database import Base

# Import all models for migration detection
from src.models import *  # noqa: F401, F403

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URLs from settings
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))

# Model metadata for migrations
target_metadata = Base.metadata


def get_url_for_migration(is_audit=False):
    """Get the appropriate database URL for migration"""
    if is_audit:
        url = settings.audit_database_url
    else:
        url = settings.database_url

    # Remove async driver for alembic (uses sync driver)
    return url.replace("+asyncpg", "")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    This configures the context with just a URL and not an Engine.
    """
    url = get_url_for_migration()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Create an Engine and associate a connection with the context.
    """
    # Determine which database to migrate
    migration_file = context.get_x_argument(as_dictionary=True).get(
        "migration_file", ""
    )
    is_audit = "audit" in migration_file.lower() if migration_file else False

    # Get the appropriate URL
    url = get_url_for_migration(is_audit)

    # Override config URL
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_for_both_databases() -> None:
    """
    Run migrations for both main and audit databases.
    This is the recommended approach for production.
    """
    # First, migrate main database
    print("🔄 Running migrations for MAIN database...")
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url_for_migration(is_audit=False)

    main_engine = create_engine(
        get_url_for_migration(is_audit=False),
        poolclass=pool.NullPool,
    )

    with main_engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    print("✓ Main database migrations completed")

    # Then, migrate audit database
    print("🔄 Running migrations for AUDIT database...")
    configuration["sqlalchemy.url"] = get_url_for_migration(is_audit=True)

    audit_engine = create_engine(
        get_url_for_migration(is_audit=True),
        poolclass=pool.NullPool,
    )

    with audit_engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    print("✓ Audit database migrations completed")


# Determine which migration mode to use
if context.is_offline_mode():
    run_migrations_offline()
else:
    # Check if we should migrate both databases
    run_both = context.get_x_argument(as_dictionary=True).get("both_dbs", "true")

    if run_both.lower() == "true":
        run_migrations_for_both_databases()
    else:
        run_migrations_online()
