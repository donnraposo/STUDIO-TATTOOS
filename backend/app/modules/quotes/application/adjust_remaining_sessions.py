import uuid
from decimal import Decimal

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_origin import QuoteOrigin
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.domain.session_plan import SessionPlan
from app.modules.quotes.domain.session_policy import SessionPolicy
from app.modules.quotes.domain.session_status import SessionStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.quotes.infrastructure.tattoo_session_repository import TattooSessionRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class AdjustRemainingSessions:
    """O gestor refaz o que falta depois de uma sessão parcial (RN-ORC-006).

    Uma sessão interrompida cobra menos do que previa, e o que sobra do trabalho
    deixa de caber no plano original. A regra não manda o sistema recalcular
    sozinho: manda o gestor ajustar. É decisão humana — pode virar uma sessão a
    mais, pode virar um desconto, pode virar nada —, e o sistema registra a
    decisão em vez de adivinhá-la.

    **Se o ajuste muda o valor total, o orçamento volta a Pendente.** É a mesma
    consequência da `UpdateQuote`, pelo mesmo motivo: o percentual congelado
    pertence a um valor aprovado, e mudar o valor sem reaprovar deixaria um
    acordo velho valendo sobre um trabalho novo (RN-REP-006).

    **O ajuste é provisório até a reaprovação.** As sessões criadas aqui são
    agendadas, e a reaprovação as refaz conforme o plano do orçamento. Isso não
    é perda: entre o ajuste e a reaprovação, quem manda é o orçamento, e é ele
    que o gestor edita para consolidar o que decidiu."""

    def __init__(
        self,
        sessions: TattooSessionRepository,
        quotes: QuoteRepository,
        policy: SessionPolicy,
        plan: SessionPlan,
        audit: AuditRecorder,
    ) -> None:
        self._sessions = sessions
        self._quotes = quotes
        self._policy = policy
        self._plan = plan
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        quote_id: uuid.UUID,
        planned_values: list[Decimal],
    ) -> list[TattooSession]:
        if not self._policy.can_adjust(actor):
            raise PermissionDeniedError("Only the studio management can adjust sessions.")

        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if quote.status != QuoteStatus.APPROVED:
            raise BusinessRuleError("Only the sessions of an approved quote can be adjusted.")

        self._ensure_values_are_amounts(planned_values)

        existing = self._sessions.list_for_quote(quote_id)
        settled = [record for record in existing if record.status != SessionStatus.SCHEDULED]
        for record in existing:
            if record.status == SessionStatus.SCHEDULED:
                self._sessions.remove(record)

        created = self._create(quote, settled, planned_values)
        total = self._plan.committed_total(
            [self._value_of(record) for record in settled], planned_values
        )

        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_SESSIONS_ADJUSTED",
            module="quotes",
            entity_type="quote",
            entity_id=str(quote.id),
            old_values={"total_value": str(quote.total_value)},
            new_values={
                "committed_total": str(total),
                "remaining_sessions": len(planned_values),
                "settled_sessions": len(settled),
            },
        )

        if total != quote.total_value:
            self._send_back_for_approval(actor, quote, total)

        return created

    @staticmethod
    def _ensure_values_are_amounts(planned_values: list[Decimal]) -> None:
        """Sessão prevista de valor zero não é sessão; é uma linha que entraria
        no repasse rendendo nada e confundindo a contagem."""
        if any(value <= 0 for value in planned_values):
            raise BusinessRuleError("Every remaining session must be worth more than zero.")

    @staticmethod
    def _value_of(record: TattooSession) -> Decimal:
        """O que a sessão compromete: o cobrado quando já houve cobrança, o
        previsto enquanto não houve. Somar o previsto de uma parcial contaria
        dinheiro que não entrou (RN-ORC-006)."""
        return record.charged_value if record.charged_value is not None else record.planned_value

    def _create(
        self, quote: Quote, settled: list[TattooSession], planned_values: list[Decimal]
    ) -> list[TattooSession]:
        percentage = quote.artist_percentage
        if percentage is None:
            raise BusinessRuleError("An approved quote must carry the frozen artist share.")

        sequence = self._plan.next_sequence([record.sequence_number for record in settled])
        return [
            self._sessions.persist(
                TattooSession(
                    quote_id=quote.id,
                    sequence_number=sequence + offset,
                    status=SessionStatus.SCHEDULED,
                    origin=QuoteOrigin(quote.origin),
                    planned_value=value,
                    artist_percentage=percentage,
                )
            )
            for offset, value in enumerate(planned_values)
        ]

    def _send_back_for_approval(
        self, actor: AuthenticatedUser, quote: Quote, total: Decimal
    ) -> None:
        """Volta a pendente sem deixar resíduo da decisão anterior, como na
        `UpdateQuote`. Manter o percentual num orçamento pendente pareceria
        inofensivo e permitiria que a próxima aprovação passasse sem regravá-lo,
        aplicando o acordo velho ao trabalho novo."""
        quote.status = QuoteStatus.PENDING
        quote.artist_percentage = None
        quote.approved_at = None
        quote.approved_by = None
        quote.rejection_reason = None
        quote.rejection_note = None
        self._quotes.persist(quote)

        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_REOPENED_BY_ADJUSTMENT",
            module="quotes",
            entity_type="quote",
            entity_id=str(quote.id),
            old_values={"status": str(QuoteStatus.APPROVED)},
            new_values={"status": str(QuoteStatus.PENDING), "committed_total": str(total)},
            reason="The adjusted sessions no longer add up to the approved total.",
        )
