import uuid
from decimal import Decimal

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class SetArtistPercentage:
    """Define o acordo de percentual de um artista (RN-CLI-003 e ADR-030).

    **Só gerente e proprietário.** A RN-CLI-003 reserva a alteração de percentual
    à gestão, e aqui vale com mais força: este número decide quanto o artista
    recebe em todo trabalho que ele aprovar daqui para frente. Deixar o próprio
    artista mexer seria deixá-lo escrever o próprio contrato.

    **Não alcança trabalho já aprovado.** A RN-REP-006 é explícita, e a garantia
    não está nesta classe: está na cópia que o orçamento congelou na aprovação.
    Mudar o acordo hoje não toca em nada que já foi acordado — o que não vale
    como desculpa para mudar sem registro, e por isso a auditoria guarda o valor
    anterior.

    **Nulo devolve o artista à regra da origem** — 70% para cliente próprio, 50%
    para indicação. É assim que um acordo é encerrado, e não apagando a conta."""

    def __init__(
        self,
        users: UserRepository,
        audit: AuditRecorder,
    ) -> None:
        self._users = users
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        artist_id: uuid.UUID,
        percentage: Decimal | None,
    ) -> UserAccount:
        if not actor.is_staff:
            raise PermissionDeniedError(
                "Only the studio management can change an artist's share."
            )

        artist = self._users.find_by_id(artist_id)
        if artist is None:
            raise BusinessRuleError("Account not found.")

        if not (artist.acts_as_artist or artist.role in ("RESIDENT", "GUEST")):
            raise BusinessRuleError("This account does not tattoo, so it has no share.")

        if percentage is not None and not (0 < percentage <= 100):
            raise BusinessRuleError("The share must be between 0 and 100 percent.")

        previous = artist.default_artist_percentage
        artist.default_artist_percentage = percentage
        self._users.add(artist)

        self._audit.record(
            actor_id=actor.id,
            action="ARTIST_PERCENTAGE_SET",
            module="identity",
            entity_type="user_account",
            entity_id=str(artist.id),
            old_values={"default_artist_percentage": str(previous) if previous else None},
            new_values={
                "default_artist_percentage": str(percentage) if percentage else None
            },
        )
        return artist
