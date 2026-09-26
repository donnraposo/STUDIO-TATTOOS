from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.settings import Settings


class DatabaseProvisioner:
    """Provisiona um banco isolado para a suite. Os testes nunca tocam o banco
    de desenvolvimento, e as migracoes reais sao aplicadas — SQLite nao
    substituiria, pois o projeto depende de CITEXT, tstzrange e EXCLUDE."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def settings(self) -> Settings:
        return self._settings

    def create(self) -> None:
        maintenance_url = self._settings.database_url.rsplit("/", 1)[0] + "/postgres"
        engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": self._settings.postgres_db},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{self._settings.postgres_db}"'))
        engine.dispose()

    def migrate(self) -> None:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", self._settings.database_url)
        command.upgrade(config, "head")

    def clear(self) -> None:
        """TRUNCATE em vez de DELETE: o gatilho append-only de audit_log recusa
        DELETE, mas TRUNCATE e DDL e nao dispara gatilhos de linha."""
        engine = create_engine(self._settings.database_url)
        tables = (
            "audit_log",
            "booking",
            "booth",
            "client",
            "password_reset_token",
            "user_status_history",
            "user_session",
            "user_account",
        )
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))
        engine.dispose()
