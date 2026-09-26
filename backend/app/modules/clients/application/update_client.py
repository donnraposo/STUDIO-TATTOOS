import uuid

from app.modules.clients.domain.client_visibility_policy import ClientVisibilityPolicy
from app.modules.clients.infrastructure.client_repository import ClientRepository
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class UpdateClient:
    """Corrige nome, telefone e Instagram (RN-CLI-006).

    O artista altera apenas os clientes que cadastrou; gestor altera qualquer um.
    Toda edição fica registrada com responsável e valores anteriores."""

    def __init__(
        self,
        clients: ClientRepository,
        policy: ClientVisibilityPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._clients = clients
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        client_id: uuid.UUID,
        name: str,
        phone: str,
        instagram: str | None,
    ) -> Client:
        client = self._clients.find_by_id(client_id)
        if client is None or client.merged_into_id is not None:
            raise BusinessRuleError("Client not found.")

        if not self._policy.can_edit(actor, client.registered_by_artist_id):
            raise PermissionDeniedError("You cannot edit this client.")

        previous = {
            "name": client.name,
            "phone": client.phone,
            "instagram": client.instagram,
        }
        client.name = name.strip()
        client.phone = phone.strip()
        client.instagram = instagram.strip() if instagram else None
        self._clients.add(client)

        self._audit.record(
            actor_id=actor.id,
            action="CLIENT_UPDATED",
            module="clients",
            entity_type="client",
            entity_id=str(client.id),
            old_values=previous,
            new_values={
                "name": client.name,
                "phone": client.phone,
                "instagram": client.instagram,
            },
        )
        return client
