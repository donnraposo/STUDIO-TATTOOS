import uuid
from datetime import UTC, datetime

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.domain.booking_status import BookingStatus
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

    **Pendência conhecida:** a RN-AGE-005 exige sinal confirmado antes de
    aprovar. O módulo de pagamentos é a sprint M5; o portão financeiro entra
    naquele momento, no ponto marcado por `_deposit_is_confirmed`."""

    def __init__(
        self,
        bookings: BookingRepository,
        policy: SchedulingPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._bookings = bookings
        self._policy = policy
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, booking_id: uuid.UUID) -> Booking:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError("Only the studio management can approve bookings.")

        booking = self._bookings.find_by_id(booking_id)
        if booking is None:
            raise BusinessRuleError("Booking not found.")

        if booking.status != BookingStatus.REQUESTED:
            raise BusinessRuleError("Only a pending request can be approved.")

        if not self._deposit_is_confirmed(booking):
            raise BusinessRuleError("The deposit must be confirmed before approval.")

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

    @staticmethod
    def _deposit_is_confirmed(booking: Booking) -> bool:
        """Costura para a sprint M5.

        Enquanto o módulo de pagamentos não existe, não há como consultar o
        sinal, e travar a aprovação aqui impediria qualquer uso da agenda. A
        verificação real substitui este ponto na M5, sem alterar o restante do
        caso de uso."""
        return True
