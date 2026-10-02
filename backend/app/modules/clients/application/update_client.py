import uuid

from app.modules.clients.domain.client_source import ClientSource
from app.modules.clients.domain.client_source_resolver import ClientSourceResolver
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
    Toda edição fica registrada com responsável e valores anteriores.

    **Corrigir quem trouxe o cliente é do gestor**, e por isso é opcional aqui:
    omitido, o campo fica como está. A RN-CLI-003 reserva a alteração de origem a
    gerente e proprietário, e quem trouxe o cliente é o que informa a origem de
    todo atendimento futuro dele — deixar o artista mexer nisso seria deixá-lo
    redesenhar o próprio repasse.

    Contato e origem são corrigidos pela mesma rota porque são a mesma ficha, mas
    passam por alçadas diferentes, e a diferença está explícita abaixo."""

    def __init__(
        self,
        clients: ClientRepository,
        policy: ClientVisibilityPolicy,
        sources: ClientSourceResolver,
        audit: AuditRecorder,
    ) -> None:
        self._clients = clients
        self._policy = policy
        self._sources = sources
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        client_id: uuid.UUID,
        name: str,
        phone: str,
        instagram: str | None,
        source: ClientSource | None = None,
        brought_by_artist_id: uuid.UUID | None = None,
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
            "brought_by_artist_id": str(client.brought_by_artist_id)
            if client.brought_by_artist_id
            else None,
        }
        client.name = name.strip()
        client.phone = phone.strip()
        client.instagram = instagram.strip() if instagram else None
        if source is not None:
            client.brought_by_artist_id = self._resolve_source(
                actor, source, brought_by_artist_id
            )
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
                "brought_by_artist_id": str(client.brought_by_artist_id)
                if client.brought_by_artist_id
                else None,
            },
        )
        return client

    def _resolve_source(
        self,
        actor: AuthenticatedUser,
        source: ClientSource,
        brought_by_artist_id: uuid.UUID | None,
    ) -> uuid.UUID | None:
        """RN-CLI-003: alterar a origem é de gerente e proprietário.

        A checagem é aqui e não na política de edição porque corrigir o telefone
        continua sendo do artista que cadastrou. São duas alçadas na mesma
        rota."""
        if not actor.is_staff:
            raise PermissionDeniedError(
                "Only the studio management can change who brought the client."
            )
        return self._sources.resolve(actor, source, brought_by_artist_id)
