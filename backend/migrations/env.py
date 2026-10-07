from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.orm_registry import METADATA
from app.core.settings import Settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Só define a URL padrão quando quem invoca não escolheu uma. Sem isso, a suite
# de testes não conseguiria migrar seu próprio banco isolado.
if not config.get_main_option("sqlalchemy.url", None):
    config.set_main_option("sqlalchemy.url", Settings().database_url)

target_metadata = METADATA


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
