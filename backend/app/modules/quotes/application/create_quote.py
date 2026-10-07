import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_details import QuoteDetails
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.permission_denied_error import PermissionDeniedError


class CreateQuote:
    """Cria um orçamento em Pendente (RN-ORC-002 e RN-ORC-004).

    Nasce sempre pendente, inclusive quando quem cria é o próprio gestor: a
    aprovação é o ato que congela o percentual, e juntar as duas coisas na
    criação tiraria do registro a data e o responsável pela decisão.

    O percentual **não** é gravado aqui. Enquanto o orçamento está pendente ele
    fica nulo, e a restrição do banco garante que só um orçamento aprovado o
    tenha (RN-REP-006)."""

    def __init__(
        self,
        quotes: QuoteRepository,
        policy: QuotePolicy,
        audit: AuditRecorder,
    ) -> None:
        self._quotes = quotes
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        client_id: uuid.UUID,
        details: QuoteDetails,
        artist_id: uuid.UUID | None = None,
    ) -> Quote:
        if not self._policy.can_create(actor):
            raise PermissionDeniedError("You cannot create quotes.")

        quote = Quote(
            client_id=client_id,
            artist_id=self._resolve_artist(actor, artist_id),
            created_by=actor.id,
            origin=details.origin,
            description=details.description,
            body_region=details.body_region,
            size_estimate=details.size_estimate,
            total_value=details.total_value,
            planned_sessions=details.planned_sessions,
            planned_value_per_session=details.planned_value_per_session,
            estimated_duration_minutes=details.estimated_duration_minutes,
            notes=details.notes,
            status=QuoteStatus.PENDING,
        )
        self._quotes.persist(quote)

        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_CREATED",
            module="quotes",
            entity_type="quote",
            entity_id=str(quote.id),
            new_values={
                "status": str(QuoteStatus.PENDING),
                "origin": str(details.origin),
                "total_value": str(details.total_value),
                "artist_id": str(quote.artist_id),
            },
        )
        return quote

    def _resolve_artist(
        self, actor: AuthenticatedUser, artist_id: uuid.UUID | None
    ) -> uuid.UUID:
        """O residente orça para si; o gestor orça para qualquer artista.

        É o que atende à RN-ORC-001 no caso do guest: ele não acessa orçamento,
        então o gestor cria em nome dele quando o estúdio indica o cliente."""
        if artist_id is None:
            return actor.id
        if artist_id != actor.id and not actor.is_staff:
            raise PermissionDeniedError("You cannot quote on behalf of another artist.")
        return artist_id
