import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.artist_percentage_policy import ArtistPercentagePolicy
from app.modules.quotes.domain.quote_origin import QuoteOrigin
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ApproveQuote:
    """Aprova o orçamento e congela o percentual do artista (RN-REP-006).

    Aprovar e congelar são o mesmo ato. A partir daqui, mudar o percentual
    padrão do estúdio não alcança este trabalho: o repasse vai ler a cópia
    gravada, não a tabela de percentuais vigente na data do cálculo.

    `artist_percentage` permite ao gestor corrigir o percentual deste
    atendimento, como a RN-CLI-003 prevê. Omitido, vale o padrão da origem. A
    correção fica na auditoria junto do valor que teria sido aplicado — um
    percentual fora do padrão precisa ser rastreável, ou vira um acordo
    particular sem registro."""

    def __init__(
        self,
        quotes: QuoteRepository,
        policy: QuotePolicy,
        percentages: ArtistPercentagePolicy,
        audit: AuditRecorder,
    ) -> None:
        self._quotes = quotes
        self._policy = policy
        self._percentages = percentages
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        quote_id: uuid.UUID,
        artist_percentage: Decimal | None = None,
    ) -> Quote:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError("Only the studio management can approve quotes.")

        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if quote.status != QuoteStatus.PENDING:
            raise BusinessRuleError("Only a pending quote can be approved.")

        standard = self._percentages.for_origin(QuoteOrigin(quote.origin))
        frozen = artist_percentage if artist_percentage is not None else standard

        quote.status = QuoteStatus.APPROVED
        quote.artist_percentage = frozen
        quote.approved_at = datetime.now(UTC)
        quote.approved_by = actor.id
        self._quotes.persist(quote)

        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_APPROVED",
            module="quotes",
            entity_type="quote",
            entity_id=str(quote.id),
            old_values={"status": str(QuoteStatus.PENDING), "artist_percentage": None},
            new_values={
                "status": str(QuoteStatus.APPROVED),
                "artist_percentage": str(frozen),
                "standard_for_origin": str(standard),
            },
        )
        return quote
