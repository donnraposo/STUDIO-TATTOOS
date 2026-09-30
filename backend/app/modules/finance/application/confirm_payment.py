import uuid
from datetime import UTC, datetime

from app.modules.finance.application.payment_decision import PaymentDecision
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.infrastructure.models.payment import Payment
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder


class ConfirmPayment:
    """Confirma o recebimento (RN-PAG-002 e RN-PAG-007).

    É a metade que destrava o resto: sem pagamento confirmado o agendamento não
    pode ser aprovado (RN-AGE-005), e sem ele a sessão não entra em repasse
    (RN-PAG-008).

    A restrição `ck_payment_confirmed_requires_actor` garante no banco que
    confirmado não existe sem quem confirmou e quando — mesmo que alguém remova
    estas linhas, não há como gravar dinheiro entrando sem responsável."""

    def __init__(
        self,
        payments: PaymentRepository,
        decision: PaymentDecision,
        audit: AuditRecorder,
    ) -> None:
        self._payments = payments
        self._decision = decision
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, payment_id: uuid.UUID) -> Payment:
        payment = self._decision.prepare(actor, payment_id, PaymentStatus.CONFIRMED)

        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_at = datetime.now(UTC)
        payment.confirmed_by = actor.id
        self._payments.persist(payment)

        self._audit.record(
            actor_id=actor.id,
            action="PAYMENT_CONFIRMED",
            module="finance",
            entity_type="payment",
            entity_id=str(payment.id),
            old_values={"status": str(PaymentStatus.REPORTED)},
            new_values={"status": str(PaymentStatus.CONFIRMED), "amount": str(payment.amount)},
        )
        return payment
