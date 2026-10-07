import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_details import QuoteDetails
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class UpdateQuote:
    """Edita o orçamento e, se ele já tinha decisão, o devolve a Pendente
    (RN-ORC-003).

    Este é o caso de uso onde a RN-REP-006 pode ser silenciosamente quebrada. Ao
    voltar para pendente, a decisão anterior é **apagada por inteiro** —
    percentual congelado, data e responsável. Manter o percentual antigo num
    orçamento pendente pareceria inofensivo e seria o contrário: a próxima
    aprovação poderia passar sem regravá-lo, e o trabalho novo sairia com o
    acordo velho.

    A restrição `ck_quote_approved_freezes_percentage` é a rede embaixo disso:
    mesmo que alguém remova estas linhas, o banco recusa um aprovado sem
    percentual.

    Um orçamento rejeitado também volta a pendente ao ser editado: é justamente
    o caminho de corrigir o que motivou a recusa e submeter de novo."""

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
        quote_id: uuid.UUID,
        details: QuoteDetails,
    ) -> Quote:
        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if not self._policy.can_edit(actor, quote.artist_id, QuoteStatus(quote.status)):
            raise PermissionDeniedError("You cannot edit this quote.")

        previous = self._snapshot(quote)
        self._apply(quote, details)
        self._discard_previous_decision(quote)
        self._quotes.persist(quote)

        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_UPDATED",
            module="quotes",
            entity_type="quote",
            entity_id=str(quote.id),
            old_values=previous,
            new_values=self._snapshot(quote),
        )
        return quote

    @staticmethod
    def _snapshot(quote: Quote) -> dict[str, object]:
        """O que a auditoria precisa comparar: estado, origem, valor e acordo."""
        return {
            "status": str(quote.status),
            "origin": str(quote.origin),
            "total_value": str(quote.total_value),
            "planned_sessions": quote.planned_sessions,
            "artist_percentage": str(quote.artist_percentage)
            if quote.artist_percentage is not None
            else None,
        }

    @staticmethod
    def _apply(quote: Quote, details: QuoteDetails) -> None:
        quote.origin = details.origin
        quote.description = details.description
        quote.body_region = details.body_region
        quote.size_estimate = details.size_estimate
        quote.total_value = details.total_value
        quote.planned_sessions = details.planned_sessions
        quote.planned_value_per_session = details.planned_value_per_session
        quote.estimated_duration_minutes = details.estimated_duration_minutes
        quote.notes = details.notes

    @staticmethod
    def _discard_previous_decision(quote: Quote) -> None:
        """Volta a pendente sem deixar resíduo da decisão anterior."""
        quote.status = QuoteStatus.PENDING
        quote.artist_percentage = None
        quote.approved_at = None
        quote.approved_by = None
        quote.rejection_reason = None
        quote.rejection_note = None
