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


class CancelBooking:
    """Cancela ou marca não comparecimento (RN-AGE-009 e RN-AGE-010).

    Ambos os estados liberam a agenda e preservam o registro. A consequência
    financeira — estúdio retém o sinal de €50 e devolve o excedente — é
    executada pelo módulo de pagamentos na sprint M5. Aqui fica o estado, que é
    o que aquele módulo vai consultar."""

    _FINAL_STATES = frozenset(
        {BookingStatus.CANCELLED, BookingStatus.NO_SHOW, BookingStatus.REJECTED}
    )

    def __init__(
        self,
        bookings: BookingRepository,
        policy: SchedulingPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._bookings = bookings
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        booking_id: uuid.UUID,
        reason: str,
        no_show: bool = False,
    ) -> Booking:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError(
                "Only the studio management can cancel a booking. Artists request it."
            )

        booking = self._bookings.find_by_id(booking_id)
        if booking is None:
            raise BusinessRuleError("Booking not found.")

        if booking.status in self._FINAL_STATES:
            raise BusinessRuleError("This booking is already closed.")

        previous = str(booking.status)
        booking.status = BookingStatus.NO_SHOW if no_show else BookingStatus.CANCELLED
        booking.decided_at = datetime.now(UTC)
        booking.decided_by = actor.id
        self._bookings.persist(booking)

        self._audit.record(
            actor_id=actor.id,
            action="BOOKING_NO_SHOW" if no_show else "BOOKING_CANCELLED",
            module="scheduling",
            entity_type="booking",
            entity_id=str(booking.id),
            old_values={"status": previous},
            new_values={"status": str(booking.status)},
            reason=reason,
        )
        return booking
