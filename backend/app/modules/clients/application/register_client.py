import uuid

from app.modules.clients.domain.client_source import ClientSource
from app.modules.clients.domain.client_source_resolver import ClientSourceResolver
from app.modules.clients.domain.client_visibility_policy import ClientVisibilityPolicy
from app.modules.clients.infrastructure.client_repository import ClientRepository
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.permission_denied_error import PermissionDeniedError


class RegisterClient:
    """Cadastra um cliente. Nome e telefone são obrigatórios; Instagram é
    opcional (RN-CLI-001).

    A duplicidade é apenas alertada, nunca bloqueada (RN-CLI-005): dois clientes
    podem legitimamente compartilhar um telefone, e travar o cadastro
    atrapalharia o atendimento.

    **Quem trouxe o cliente é gravado aqui, e não se confunde com quem
    cadastrou** (RN-CLI-002). Os dois coincidem quando o artista cadastra o
    próprio cliente e divergem no caso que importa: a RN-GST-005 manda o gestor
    cadastrar o cliente indicado pelo estúdio, e ali quem digitou não trouxe
    ninguém. O padrão é `ARTIST` sem artista informado, isto é, o próprio ator —
    o caso corrente."""

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
        name: str,
        phone: str,
        instagram: str | None = None,
        source: ClientSource = ClientSource.ARTIST,
        brought_by_artist_id: uuid.UUID | None = None,
    ) -> tuple[Client, list[Client]]:
        if not self._policy.can_register(actor):
            raise PermissionDeniedError("You cannot register clients.")

        brought_by = self._sources.resolve(actor, source, brought_by_artist_id)

        normalized_phone = phone.strip()
        normalized_instagram = instagram.strip() if instagram else None
        duplicates = self._clients.find_possible_duplicates(
            phone=normalized_phone, instagram=normalized_instagram
        )

        client = self._clients.add(
            Client(
                name=name.strip(),
                phone=normalized_phone,
                instagram=normalized_instagram,
                registered_by_artist_id=actor.id,
                brought_by_artist_id=brought_by,
            )
        )

        self._audit.record(
            actor_id=actor.id,
            action="CLIENT_REGISTERED",
            module="clients",
            entity_type="client",
            entity_id=str(client.id),
            new_values={
                "name": client.name,
                "phone": client.phone,
                "brought_by_artist_id": str(brought_by) if brought_by else None,
            },
        )
        return client, duplicates
