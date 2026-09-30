import uuid

from app.modules.finance.domain.deposit_policy import DepositPolicy
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.scheduling.domain.deposit_gate import DepositGate
from app.shared.errors.business_rule_error import BusinessRuleError


class PaymentDepositGate(DepositGate):
    """A resposta do financeiro ao portão da agenda (RN-AGE-005 e RN-PAG-002).

    Implementa a porta que a agenda declarou. É aqui que as duas metades se
    encontram, e só aqui: a agenda continua sem conhecer pagamento, e o
    financeiro continua sem conhecer aprovação.

    Duas perguntas, nesta ordem, porque a segunda só faz sentido depois da
    primeira: *este agendamento exige sinal?* e *o sinal está confirmado?*

    A primeira existe pela RN-GST-004 — o guest recebe diretamente dos clientes
    próprios e esses valores não passam pelo estúdio, então exigir deles um sinal
    confirmado pelo gestor faria o estúdio receber dinheiro que a regra diz não
    passar por ele."""

    def __init__(
        self,
        payments: PaymentRepository,
        users: UserRepository,
        policy: DepositPolicy,
    ) -> None:
        self._payments = payments
        self._users = users
        self._policy = policy

    def is_required_for(self, artist_id: uuid.UUID, belongs_to_quoted_work: bool) -> bool:
        artist = self._users.find_by_id(artist_id)
        if artist is None:
            raise BusinessRuleError("The artist of this booking no longer exists.")
        return self._policy.requires_deposit(UserRole(artist.role), belongs_to_quoted_work)

    def is_satisfied_for(
        self, booking_id: uuid.UUID, artist_id: uuid.UUID, belongs_to_quoted_work: bool
    ) -> bool:
        if not self.is_required_for(artist_id, belongs_to_quoted_work):
            return True

        deposit = self._payments.find_live_deposit(booking_id)
        return deposit is not None and PaymentStatus(deposit.status) == PaymentStatus.CONFIRMED
