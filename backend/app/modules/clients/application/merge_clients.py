import uuid

from app.modules.clients.domain.client_visibility_policy import ClientVisibilityPolicy
from app.modules.clients.infrastructure.client_repository import ClientRepository
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class MergeClients:
    """Une cadastros duplicados, preservando vínculos e histórico (RN-CLI-006).

    O duplicado não é apagado: recebe `merged_into_id` apontando para o
    sobrevivente. Apagar quebraria agendamentos, sessões e pagamentos já ligados
    a ele, e a regra proíbe exclusão de cliente com histórico."""

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
        self, actor: AuthenticatedUser, duplicate_id: uuid.UUID, survivor_id: uuid.UUID
    ) -> Client:
        if not self._policy.can_merge(actor):
            raise PermissionDeniedError("Only the studio management can merge clients.")

        if duplicate_id == survivor_id:
            raise BusinessRuleError("A client cannot be merged into itself.")

        duplicate = self._clients.find_by_id(duplicate_id)
        survivor = self._clients.find_by_id(survivor_id)
        if duplicate is None or survivor is None:
            raise BusinessRuleError("Client not found.")

        if duplicate.merged_into_id is not None:
            raise BusinessRuleError("This client has already been merged.")
        if survivor.merged_into_id is not None:
            raise BusinessRuleError("The surviving client has itself been merged.")

        duplicate.merged_into_id = survivor.id
        self._clients.add(duplicate)

        self._audit.record(
            actor_id=actor.id,
            action="CLIENT_MERGED",
            module="clients",
            entity_type="client",
            entity_id=str(duplicate.id),
            new_values={"merged_into": str(survivor.id)},
        )
        return survivor
