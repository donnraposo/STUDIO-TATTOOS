import uuid
from datetime import UTC, datetime

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.domain.booking_status import BookingStatus
from app.modules.scheduling.domain.rejection_reason import RejectionReason
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository
from app.modules.scheduling.infrastructure.models.booking import Booking
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class RejectBooking:
    """Recusa uma solicitação (RN-AGE-006).

    O motivo vem de lista fechada porque alimenta o tratamento financeiro do
    sinal: recusa pelo estúdio devolve o valor integralmente (RN-PAG-003).

    Rejeitar libera a agenda do artista — o registro permanece como histórico,
    mas sai da cláusula `WHERE` das restrições (RN-AGE-014)."""

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
        reason: RejectionReason,
        note: str | None = None,
    ) -> Booking:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError("Only the studio management can reject bookings.")

        booking = self._bookings.find_by_id(booking_id)
        if booking is None:
            raise BusinessRuleError("Booking not found.")

        if booking.status != BookingStatus.REQUESTED:
            raise BusinessRuleError("Only a pending request can be rejected.")

        booking.status = BookingStatus.REJECTED
        booking.rejection_reason = str(reason)
        booking.rejection_note = note.strip() if note else None
        booking.decided_at = datetime.now(UTC)
        booking.decided_by = actor.id
        self._bookings.persist(booking)

        self._audit.record(
            actor_id=actor.id,
            action="BOOKING_REJECTED",
            module="scheduling",
            entity_type="booking",
            entity_id=str(booking.id),
            new_values={"status": str(BookingStatus.REJECTED), "reason": str(reason)},
            reason=note,
        )
        return booking
