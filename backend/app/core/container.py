from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.core.csrf_guard import CsrfGuard
from app.core.database import Database

# Importado pelo efeito de registrar todos os modelos no metadata antes de
# qualquer gravacao. Ver o modulo para o defeito que isto evita.
from app.core.orm_registry import METADATA  # noqa: F401
from app.core.settings import Settings
from app.modules.clients.clients_factory import ClientsFactory
from app.modules.finance.finance_factory import FinanceFactory
from app.modules.identity.identity_factory import IdentityFactory
from app.modules.quotes.application.quote_settled_sessions import QuoteSettledSessions
from app.modules.quotes.quotes_factory import QuotesFactory
from app.modules.scheduling.scheduling_factory import SchedulingFactory
from app.shared.storage.filesystem_object_storage import FilesystemObjectStorage
from app.shared.storage.object_storage import ObjectStorage


class Container:
    """Raiz de composicao. Constroi e mantem as dependencias de infraestrutura
    em um unico lugar, para que os modulos dependam de abstracoes e nao saibam
    como elas sao instanciadas.

    Cada modulo de negocio expoe a propria fabrica; o container apenas as reune,
    para nao concentrar o conhecimento interno de todos os dominios."""

    _instance: "Container | None" = None

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._database = Database(url=self._settings.database_url, echo=self._settings.debug)
        self._csrf_guard = CsrfGuard(
            cookie_name=self._settings.csrf_cookie_name,
            header_name=self._settings.csrf_header_name,
        )
        self._identity = IdentityFactory(self._settings)
        self._clients = ClientsFactory()
        # O repasse pergunta ao orcamento o que foi quitado; os dois se
        # encontram aqui, pela porta que o financeiro declarou (ADR-028).
        self._finance = FinanceFactory(settled_sessions=QuoteSettledSessions)
        # A agenda recebe as portas, nao o modulo financeiro: e aqui, na raiz de
        # composicao, que os dois se encontram (ADR-016).
        self._scheduling = SchedulingFactory(
            deposit_gate=self._finance.deposit_gate,
            settlement_gate=self._finance.settlement_gate,
        )
        self._storage: ObjectStorage = FilesystemObjectStorage(self._settings.storage_root)
        self._quotes = QuotesFactory(settings=self._settings, storage=self._storage)

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

    @property
    def csrf_guard(self) -> CsrfGuard:
        return self._csrf_guard

    @property
    def identity(self) -> IdentityFactory:
        return self._identity

    @property
    def clients(self) -> ClientsFactory:
        return self._clients

    @property
    def scheduling(self) -> SchedulingFactory:
        return self._scheduling

    @property
    def finance(self) -> FinanceFactory:
        return self._finance

    @property
    def quotes(self) -> QuotesFactory:
        return self._quotes

    @property
    def storage(self) -> ObjectStorage:
        """Exposto para que a suíte confira o armazenamento sem recriar o cliente."""
        return self._storage

    def open_session(self) -> Iterator[Session]:
        with self._database.session() as session:
            yield session
