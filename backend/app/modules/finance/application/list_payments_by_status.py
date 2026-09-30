from app.modules.finance.domain.payment_policy import PaymentPolicy
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.infrastructure.models.payment import Payment
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ListPaymentsByStatus:
    """Os pagamentos do estúdio num estado, para o painel do gestor.

    Existe separada da `ListPayments` porque a pergunta é outra. Aquela parte de
    um agendamento e responde "o que entrou por este horário"; esta parte de um
    estado e responde "o que está esperando decisão", sem agendamento em mão —
    que é justamente a pergunta de quem não sabe onde procurar (seção 10.1).

    **Só o gestor.** Confirmar recebimento é dele (RN-PAG-002), e a lista do que
    aguarda confirmação é a fila de trabalho dele. O artista acompanha os
    pagamentos dos próprios atendimentos pela `ListPayments`, que parte do
    agendamento e aplica o recorte por artista."""

    def __init__(self, payments: PaymentRepository, policy: PaymentPolicy) -> None:
        self._payments = payments
        self._policy = policy

    def execute(self, actor: AuthenticatedUser, status: PaymentStatus) -> list[Payment]:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError("Only the studio management can see this list.")

        return self._payments.list_by_status(status)
