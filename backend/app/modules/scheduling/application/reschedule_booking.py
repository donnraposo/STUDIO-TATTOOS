import uuid
from datetime import UTC, datetime

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.domain.booking_status import BookingStatus
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository
from app.modules.scheduling.infrastructure.booth_repository import BoothRepository
from app.modules.scheduling.infrastructure.models.booking import Booking
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class RescheduleBooking:
    """Move um agendamento para outro horário ou maca (RN-AGE-008).

    Somente o gestor efetiva a remarcação. O novo intervalo passa pelas mesmas
    restrições do banco, então remarcar para cima de outro agendamento é
    recusado igual a criar.

    A regra das 24 horas define o destino do sinal, não a permissão de remarcar:
    dentro do prazo os valores seguem para o novo horário, fora dele o cliente
    perde o sinal (RN-AGE-008). Esse efeito é do módulo de pagamentos, na M5."""

    def __init__(
        self,
        bookings: BookingRepository,
        booths: BoothRepository,
        policy: SchedulingPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._bookings = bookings
        self._booths = booths
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        booking_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        booth_id: uuid.UUID | None = None,
    ) -> Booking:
        if not self._policy.can_decide(actor):
            raise PermissionDeniedError("Only the studio management can reschedule.")

        if ends_at <= starts_at:
            raise BusinessRuleError("The end time must be after the start time.")

        booking = self._bookings.find_by_id(booking_id)
        if booking is None:
            raise BusinessRuleError("Booking not found.")

        if booking.status not in (BookingStatus.REQUESTED, BookingStatus.APPROVED):
            raise BusinessRuleError("Only an open booking can be rescheduled.")

        previous = {
            "period": str(booking.period),
            "booth_id": str(booking.booth_id),
        }

        if booth_id is not None:
            booth = self._booths.find_by_id(booth_id)
            if booth is None or not booth.active:
                raise BusinessRuleError("Booth not found or inactive.")
            booking.booth_id = booth_id

        booking.period = self._bookings.build_period(starts_at, ends_at)
        booking.decided_at = datetime.now(UTC)
        booking.decided_by = actor.id
        self._bookings.persist(booking)

        self._audit.record(
            actor_id=actor.id,
            action="BOOKING_RESCHEDULED",
            module="scheduling",
            entity_type="booking",
            entity_id=str(booking.id),
            old_values=previous,
            new_values={
                "period": f"{starts_at.isoformat()}/{ends_at.isoformat()}",
                "booth_id": str(booking.booth_id),
            },
        )
        return booking
