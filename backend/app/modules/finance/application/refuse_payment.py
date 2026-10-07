import uuid
from datetime import UTC, datetime

from app.modules.finance.application.payment_decision import PaymentDecision
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.infrastructure.models.payment import Payment
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError


class RefusePayment:
    """Recusa um recebimento informado (RN-PAG-007).

    O comprovante não bate, o depósito não caiu, o valor está errado: o
    lançamento é recusado com motivo e **permanece no histórico**. A regra é
    explícita — pagamento nunca é apagado.

    Recusar é estado final: um pagamento recusado que voltasse a confirmado
    apagaria a recusa, e a RN-PAG-007 manda corrigir por lançamento novo, não por
    reescrita. Recusado o sinal, o cliente paga outro, e o índice parcial
    `uq_payment_live_deposit` deixa o novo entrar."""

    def __init__(
        self,
        payments: PaymentRepository,
        decision: PaymentDecision,
        audit: AuditRecorder,
    ) -> None:
        self._payments = payments
        self._decision = decision
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, payment_id: uuid.UUID, reason: str) -> Payment:
        if not reason.strip():
            raise BusinessRuleError("Refusing a payment requires a reason.")

        payment = self._decision.prepare(actor, payment_id, PaymentStatus.REFUSED)

        payment.status = PaymentStatus.REFUSED
        payment.refused_at = datetime.now(UTC)
        payment.refused_by = actor.id
        payment.refusal_reason = reason.strip()
        self._payments.persist(payment)

        self._audit.record(
            actor_id=actor.id,
            action="PAYMENT_REFUSED",
            module="finance",
            entity_type="payment",
            entity_id=str(payment.id),
            old_values={"status": str(PaymentStatus.REPORTED)},
            new_values={"status": str(PaymentStatus.REFUSED)},
            reason=reason.strip(),
        )
        return payment
