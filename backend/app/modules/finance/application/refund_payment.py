import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.finance.application.payment_decision import PaymentDecision
from app.modules.finance.domain.payment_method import PaymentMethod
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.infrastructure.models.payment_refund import PaymentRefund
from app.modules.finance.infrastructure.payment_refund_repository import (
    PaymentRefundRepository,
)
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError


class RefundPayment:
    """Registra uma devolução já realizada (RN-PAG-009).

    **O lançamento original permanece.** A devolução nasce como linha própria,
    vinculada ao pagamento, para que o histórico mostre os três números que
    importam: quanto entrou, quanto voltou e quanto o estúdio reteve. Um saldo
    único teria apagado os outros dois.

    **A forma pode diferir da original**: um depósito devolvido em dinheiro é
    caso previsto, e por isso a forma é da devolução e não herdada.

    O gestor registra **depois** de realizar a devolução — o sistema não
    movimenta dinheiro nesta versão (RN-PAG-006)."""

    def __init__(
        self,
        payments: PaymentRepository,
        refunds: PaymentRefundRepository,
        decision: PaymentDecision,
        audit: AuditRecorder,
    ) -> None:
        self._payments = payments
        self._refunds = refunds
        self._decision = decision
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        payment_id: uuid.UUID,
        amount: Decimal,
        method: PaymentMethod,
        reason: str,
        note: str | None = None,
    ) -> PaymentRefund:
        if not reason.strip():
            raise BusinessRuleError("Registering a refund requires a reason.")

        payment = self._decision.prepare(actor, payment_id, PaymentStatus.REFUNDED)
        self._ensure_within_what_was_received(payment_id, payment.amount, amount)

        refund = self._refunds.persist(
            PaymentRefund(
                payment_id=payment.id,
                amount=amount,
                method=method,
                reason=reason.strip(),
                note=note,
                refunded_at=datetime.now(UTC),
                actor_id=actor.id,
            )
        )

        payment.status = PaymentStatus.REFUNDED
        self._payments.persist(payment)

        self._audit.record(
            actor_id=actor.id,
            action="PAYMENT_REFUNDED",
            module="finance",
            entity_type="payment",
            entity_id=str(payment.id),
            old_values={"status": str(PaymentStatus.CONFIRMED)},
            new_values={
                "status": str(PaymentStatus.REFUNDED),
                "refund_id": str(refund.id),
                "refunded_amount": str(amount),
                "method": str(method),
            },
            reason=reason.strip(),
        )
        return refund

    def _ensure_within_what_was_received(
        self, payment_id: uuid.UUID, received: Decimal, amount: Decimal
    ) -> None:
        """Não se devolve mais do que entrou.

        Soma as devoluções anteriores porque um pagamento pode ser devolvido em
        partes — o estúdio retém os €50 do sinal e devolve o restante, e o
        restante pode voltar em mais de uma vez (RN-PAG-004 e RN-AGE-009)."""
        if amount <= 0:
            raise BusinessRuleError("A refund must be greater than zero.")

        already = sum(
            (refund.amount for refund in self._refunds.list_for_payment(payment_id)),
            Decimal("0"),
        )
        if already + amount > received:
            raise BusinessRuleError(
                "A refund cannot exceed what the studio received for this payment."
            )
