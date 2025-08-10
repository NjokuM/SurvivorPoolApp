from logging.config import fileConfig
import sys, os

# Make sure we can import from app/
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from sqlalchemy import pool
from sqlalchemy import create_engine  # ✅ Sync engine for migrations
from alembic import context
from app.database import DATABASE_URL
from app.models import Base

# Alembic config
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Our model's metadata
target_metadata = Base.metadata

# Convert async URL to sync URL
def get_sync_db_url(async_url: str) -> str:
    return async_url.replace("postgresql+asyncpg", "postgresql")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_sync_db_url(DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        get_sync_db_url(DATABASE_URL),
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

# Choose mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()