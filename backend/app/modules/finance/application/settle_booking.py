import uuid
from datetime import UTC, datetime

from app.modules.finance.domain.booking_settlement import BookingSettlement
from app.modules.finance.domain.payment_kind import PaymentKind
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.domain.settlement_event import SettlementEvent
from app.modules.finance.infrastructure.models.payment import Payment
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder


class SettleBooking:
    """Aplica ao dinheiro o desfecho do agendamento (RN-PAG-003, RN-AGE-008,
    RN-AGE-009 e RN-AGE-010).

    **Retém automaticamente; nunca devolve automaticamente.** A diferença não é
    de estilo, é da regra. Reter é escrituração: o estúdio já está com o
    dinheiro e a RN-AGE-009 diz que ele fica, mesmo com aviso de 24 horas —
    nada se move, só se registra. Devolver é movimento de caixa, e a RN-PAG-009
    é explícita: *gerente ou proprietário registrará manualmente a devolução
    **depois de realizá-la***. Um sistema que lançasse a devolução sozinho
    estaria afirmando que o dinheiro saiu quando ninguém o mandou sair.

    O que este caso de uso faz pelo gestor é **apontar o que a regra manda
    devolver** — devolve a lista, que a interface mostra e a auditoria registra.
    Quem executa a devolução é o `RefundPayment`, com forma, motivo e
    responsável.

    O sinal retido continua `CONFIRMED`: o estúdio ficou com ele. O que a marca
    faz é tirá-lo de cena como sinal daquele horário, para que uma remarcação
    fora do prazo exija um sinal novo em vez de reaproveitar o perdido
    (RN-AGE-008)."""

    def __init__(
        self,
        payments: PaymentRepository,
        settlement: BookingSettlement,
        audit: AuditRecorder,
    ) -> None:
        self._payments = payments
        self._settlement = settlement
        self._audit = audit

    def execute(
        self, actor: AuthenticatedUser, booking_id: uuid.UUID, event: SettlementEvent
    ) -> list[Payment]:
        outcome = self._settlement.decide(event)
        if outcome.keeps_everything:
            return []

        confirmed = [
            payment
            for payment in self._payments.list_for_booking(booking_id)
            if PaymentStatus(payment.status) == PaymentStatus.CONFIRMED
            and payment.retained_at is None
        ]
        deposits = [
            payment for payment in confirmed if PaymentKind(payment.kind) == PaymentKind.DEPOSIT
        ]
        others = [
            payment for payment in confirmed if PaymentKind(payment.kind) != PaymentKind.DEPOSIT
        ]

        if outcome.retain_deposit:
            for deposit in deposits:
                self._retain(deposit, self._settlement.reason(event))

        awaiting = list(others) if outcome.refund_above_deposit else []
        if outcome.refund_deposit:
            awaiting = deposits + awaiting

        self._audit.record(
            actor_id=actor.id,
            action="BOOKING_SETTLED",
            module="finance",
            entity_type="booking",
            entity_id=str(booking_id),
            new_values={
                "event": str(event),
                "retained_deposits": len(deposits) if outcome.retain_deposit else 0,
                "awaiting_refund": [str(payment.id) for payment in awaiting],
            },
            reason=self._settlement.reason(event),
        )
        return awaiting

    def _retain(self, deposit: Payment, reason: str) -> None:
        deposit.retained_at = datetime.now(UTC)
        deposit.retained_reason = reason
        self._payments.persist(deposit)
