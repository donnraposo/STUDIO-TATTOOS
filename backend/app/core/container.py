from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.core.database import Database
from app.core.settings import Settings


class Container:
    """Raiz de composicao. Constroi e mantem as dependencias de infraestrutura
    em um unico lugar, para que os modulos dependam de abstracoes e nao saibam
    como elas sao instanciadas."""

    _instance: "Container | None" = None

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._database = Database(url=self._settings.database_url, echo=self._settings.debug)

    @classmethod
    def instance(cls) -> "Container":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Usado por testes para descartar a instancia compartilhada."""
        cls._instance = None

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def database(self) -> Database:
        return self._database

    def open_session(self) -> Iterator[Session]:
        with self._database.session() as session:
            yield session
