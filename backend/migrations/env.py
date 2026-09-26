from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.orm_base import OrmBase
from app.core.settings import Settings

# Importados para que os modelos se registrem no metadata antes do autogenerate.
from app.modules.clients.infrastructure.models.client import Client  # noqa: F401
from app.modules.identity.infrastructure.models.password_reset_token import (  # noqa: F401
    PasswordResetToken,
)
from app.modules.identity.infrastructure.models.user_account import UserAccount  # noqa: F401
from app.modules.identity.infrastructure.models.user_session import UserSession  # noqa: F401
from app.modules.identity.infrastructure.models.user_status_history import (  # noqa: F401
    UserStatusHistory,
)
from app.modules.reporting.infrastructure.models.audit_log import AuditLog  # noqa: F401
from app.modules.scheduling.infrastructure.models.booking import Booking  # noqa: F401
from app.modules.scheduling.infrastructure.models.booth import Booth  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Só define a URL padrão quando quem invoca não escolheu uma. Sem isso, a suite
# de testes não conseguiria migrar seu próprio banco isolado.
if not config.get_main_option("sqlalchemy.url", None):
    config.set_main_option("sqlalchemy.url", Settings().database_url)

target_metadata = OrmBase.metadata


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
