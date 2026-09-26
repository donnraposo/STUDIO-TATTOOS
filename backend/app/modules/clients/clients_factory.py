from sqlalchemy.orm import Session

from app.modules.clients.application.list_clients import ListClients
from app.modules.clients.application.merge_clients import MergeClients
from app.modules.clients.application.register_client import RegisterClient
from app.modules.clients.application.update_client import UpdateClient
from app.modules.clients.domain.client_visibility_policy import ClientVisibilityPolicy
from app.modules.clients.infrastructure.client_repository import ClientRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder


class ClientsFactory:
    """Monta os casos de uso do módulo de clientes."""

    def __init__(self) -> None:
        self._policy = ClientVisibilityPolicy()

    @property
    def policy(self) -> ClientVisibilityPolicy:
        return self._policy

    def clients(self, session: Session) -> ClientRepository:
        return ClientRepository(session)

    def register_client(self, session: Session) -> RegisterClient:
        return RegisterClient(
            clients=self.clients(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def list_clients(self, session: Session) -> ListClients:
        return ListClients(clients=self.clients(session), policy=self._policy)

    def update_client(self, session: Session) -> UpdateClient:
        return UpdateClient(
            clients=self.clients(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def merge_clients(self, session: Session) -> MergeClients:
        return MergeClients(
            clients=self.clients(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )
