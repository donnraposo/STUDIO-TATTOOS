import uuid
from datetime import UTC, datetime

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.domain.booking_status import BookingStatus
from app.modules.scheduling.domain.deposit_gate import DepositGate
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository
from app.modules.scheduling.infrastructure.models.booking import Booking
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ApproveBooking:
    """Aprova uma solicitação (RN-AGE-005).

    A aprovação é o momento em que a maca passa a ser bloqueada: até aqui a
    solicitação ocupava apenas a agenda do artista. Por isso é aqui que o
    conflito de maca pode aparecer, mesmo que a solicitação tenha sido aceita
    sem problema — outra pode ter sido aprovada no intervalo.

    **O sinal é conferido antes de qualquer coisa mudar** (RN-AGE-005 e
    RN-PAG-002): uma solicitação não pode ser aprovada enquanto o pagamento do
    sinal não estiver confirmado. Quem responde é o módulo financeiro, através
    da porta `DepositGate` — a agenda pergunta, não calcula.

    O horário pertence a um trabalho orçado quando tem sessão ligada. A resposta
    importa porque o agendamento de cliente próprio do guest não exige sinal
    (RN-GST-004), e é por ausência de sessão que ele se reconhece: o guest não
    acessa orçamento (RN-ORC-001), então o que o estúdio lhe indica é sempre o
    gestor quem orça."""

    def __init__(
        self,
        bookings: BookingRepository,
        policy: SchedulingPolicy,
        deposits: DepositGate,
        audit: AuditRecorder,
    ) -> None:
        self._bookings = bookings
        self._policy = policy
        self._deposits = deposits
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, booking_id: uuid.UUID) -> Booking:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError("Only the studio management can approve bookings.")

        booking = self._bookings.find_by_id(booking_id)
        if booking is None:
            raise BusinessRuleError("Booking not found.")

        if booking.status != BookingStatus.REQUESTED:
            raise BusinessRuleError("Only a pending request can be approved.")

        if not self._deposits.is_satisfied_for(
            booking.id, booking.artist_id, booking.session_id is not None
        ):
            raise BusinessRuleError(
                "The €50 deposit must be registered and confirmed before approving this booking."
            )

        booking.status = BookingStatus.APPROVED
        booking.decided_at = datetime.now(UTC)
        booking.decided_by = actor.id
        self._bookings.persist(booking)

        self._audit.record(
            actor_id=actor.id,
            action="BOOKING_APPROVED",
            module="scheduling",
            entity_type="booking",
            entity_id=str(booking.id),
            old_values={"status": str(BookingStatus.REQUESTED)},
            new_values={"status": str(BookingStatus.APPROVED)},
        )
        return booking

