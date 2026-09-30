import uuid

from app.modules.finance.domain.payment_policy import PaymentPolicy
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.domain.payment_transition import PaymentTransition
from app.modules.finance.infrastructure.models.payment import Payment
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class PaymentDecision:
    """Os três passos que **toda** decisão sobre pagamento repete: conferir a
    alçada, encontrar o lançamento e validar a mudança de estado.

    Existe porque confirmar, recusar, devolver e estornar faziam exatamente a
    mesma abertura. Copiada quatro vezes, bastaria uma esquecer a checagem de
    transição para que um pagamento recusado voltasse a confirmado — e a recusa
    sumisse do histórico, que é justamente o que a RN-PAG-007 proíbe.

    Não decide o que fazer depois: devolve o pagamento pronto para o caso de uso
    aplicar a sua parte."""

    def __init__(
        self,
        payments: PaymentRepository,
        policy: PaymentPolicy,
        transitions: PaymentTransition,
    ) -> None:
        self._payments = payments
        self._policy = policy
        self._transitions = transitions

    def prepare(
        self, actor: AuthenticatedUser, payment_id: uuid.UUID, target: PaymentStatus
    ) -> Payment:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError("Only the studio management can decide on payments.")

        payment = self._payments.find_by_id(payment_id)
        if payment is None:
            raise BusinessRuleError("Payment not found.")

        current = PaymentStatus(payment.status)
        if not self._transitions.allows(current, target):
            raise BusinessRuleError(
                f"A payment that is {current} cannot become {target}."
            )
        return payment
