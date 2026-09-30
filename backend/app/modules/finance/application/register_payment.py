import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.finance.domain.payment_kind import PaymentKind
from app.modules.finance.domain.payment_method import PaymentMethod
from app.modules.finance.domain.payment_policy import PaymentPolicy
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.infrastructure.models.payment import Payment
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class RegisterPayment:
    """Lança um recebimento informado (RN-PAG-002, RN-PAG-006 e RN-PAG-007).

    **Nasce em `REPORTED`, nunca em `CONFIRMED`.** Informar e confirmar são atos
    diferentes: o comprovante chega, o gestor confere e só então confirma. Um
    lançamento que já nascesse confirmado apagaria a conferência do histórico —
    e é sobre recebimento confirmado que a RN-AGE-005 libera a aprovação do
    horário e que o repasse do artista é calculado.

    **Só o gestor lança** (RN-PAG-006): todos os recebimentos são inseridos e
    confirmados manualmente por gerente ou proprietário nesta versão.

    A origem é exclusiva: ou o agendamento, ou a sessão. O sinal pertence ao
    agendamento, porque é o horário reservado que ele confirma (RN-PAG-001); o
    saldo pertence à sessão, porque é ela que é quitada (RN-PAG-008)."""

    def __init__(
        self,
        payments: PaymentRepository,
        policy: PaymentPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._payments = payments
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        amount: Decimal,
        kind: PaymentKind,
        method: PaymentMethod,
        booking_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        client_id: uuid.UUID | None = None,
        note: str | None = None,
    ) -> Payment:
        if not self._policy.can_register(actor):
            raise PermissionDeniedError("Only the studio management can register payments.")

        self._ensure_single_origin(kind, booking_id, session_id)
        self._ensure_no_live_deposit(kind, booking_id)

        payment = self._payments.persist(
            Payment(
                booking_id=booking_id,
                session_id=session_id,
                client_id=client_id,
                amount=amount,
                kind=kind,
                method=method,
                status=PaymentStatus.REPORTED,
                note=note,
                reported_at=datetime.now(UTC),
                reported_by=actor.id,
            )
        )

        self._audit.record(
            actor_id=actor.id,
            action="PAYMENT_REGISTERED",
            module="finance",
            entity_type="payment",
            entity_id=str(payment.id),
            new_values={
                "status": str(PaymentStatus.REPORTED),
                "kind": str(kind),
                "method": str(method),
                "amount": str(amount),
                "booking_id": str(booking_id) if booking_id else None,
                "session_id": str(session_id) if session_id else None,
            },
        )
        return payment

    def _ensure_no_live_deposit(self, kind: PaymentKind, booking_id: uuid.UUID | None) -> None:
        """Um sinal vivo por agendamento (RN-PAG-001).

        O índice parcial `uq_payment_live_deposit` é a garantia — ele resiste a
        duas requisições simultâneas, que esta checagem não veria. O que a
        checagem faz é dar a mensagem: sem ela, quem lança o segundo sinal
        recebe um erro de integridade do banco em vez de saber que já existe um.

        Recusado e retido não contam: depois de uma recusa o cliente paga outro,
        e depois de remarcar fora do prazo ele precisa pagar um novo
        (RN-AGE-008)."""
        if kind != PaymentKind.DEPOSIT or booking_id is None:
            return
        if self._payments.find_live_deposit(booking_id) is not None:
            raise BusinessRuleError("This booking already has a deposit awaiting or confirmed.")

    @staticmethod
    def _ensure_single_origin(
        kind: PaymentKind, booking_id: uuid.UUID | None, session_id: uuid.UUID | None
    ) -> None:
        """A restrição do banco recusa por último; aqui a mensagem diz o que
        fazer em vez de devolver um erro de integridade."""
        if (booking_id is None) == (session_id is None):
            raise BusinessRuleError(
                "A payment belongs either to a booking or to a session, not to both."
            )
        if kind == PaymentKind.DEPOSIT and booking_id is None:
            raise BusinessRuleError("A deposit belongs to a booking.")
