from app.modules.clients.domain.client_visibility_policy import ClientVisibilityPolicy
from app.modules.clients.infrastructure.client_repository import ClientRepository
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ListClients:
    """Lista clientes conforme o alcance de quem pergunta (RN-CLI-004).

    Gestor vê todos; artista vê apenas os que cadastrou. O recorte acontece na
    consulta, não filtrando depois de carregar tudo — assim o dado de outro
    artista nunca chega a ser lido."""

    def __init__(self, clients: ClientRepository, policy: ClientVisibilityPolicy) -> None:
        self._clients = clients
        self._policy = policy

    def execute(self, actor: AuthenticatedUser) -> list[Client]:
        if self._policy.can_list_all(actor):
            return self._clients.list_all()
        if actor.tattoos:
            return self._clients.list_registered_by(actor.id)
        raise PermissionDeniedError("You cannot list clients.")
