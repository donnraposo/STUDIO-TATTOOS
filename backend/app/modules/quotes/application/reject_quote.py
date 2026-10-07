import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class RejectQuote:
    """Rejeita o orçamento com motivo obrigatório (RN-ORC-003).

    O motivo é texto livre, diferente da recusa de agendamento, que tem lista
    fechada (RN-AGE-006). A regra de orçamento exige motivo e não enumera
    opções: as razões de recusar um valor são variadas demais para caber numa
    lista, e uma lista incompleta empurraria todo mundo para a opção 'outro'.

    Rejeitado não é o fim do caminho: editar o orçamento o devolve a pendente,
    que é como a correção é submetida de novo."""

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
        reason: str,
        note: str | None = None,
    ) -> Quote:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError("Only the studio management can reject quotes.")

        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if quote.status != QuoteStatus.PENDING:
            raise BusinessRuleError("Only a pending quote can be rejected.")

        quote.status = QuoteStatus.REJECTED
        quote.rejection_reason = reason.strip()
        quote.rejection_note = note.strip() if note else None
        self._quotes.persist(quote)

        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_REJECTED",
            module="quotes",
            entity_type="quote",
            entity_id=str(quote.id),
            old_values={"status": str(QuoteStatus.PENDING)},
            new_values={"status": str(QuoteStatus.REJECTED)},
            reason=quote.rejection_reason,
        )
        return quote
