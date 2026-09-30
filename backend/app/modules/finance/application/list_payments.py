import uuid

from app.modules.finance.domain.payment_policy import PaymentPolicy
from app.modules.finance.infrastructure.models.payment import Payment
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ListPayments:
    """Os pagamentos de um agendamento, para quem pode ver aquele agendamento.

    O artista precisa acompanhar os recebimentos dos proprios atendimentos:
    e deles que sai o repasse dele (RN-REP-007). O recorte e o mesmo da agenda
    -- gestor ve tudo, artista ve o que e seu."""

    def __init__(
        self,
        payments: PaymentRepository,
        bookings: BookingRepository,
        policy: PaymentPolicy,
    ) -> None:
        self._payments = payments
        self._bookings = bookings
        self._policy = policy

    def execute(self, actor: AuthenticatedUser, booking_id: uuid.UUID) -> list[Payment]:
        booking = self._bookings.find_by_id(booking_id)
        if booking is None:
            raise BusinessRuleError("Booking not found.")

        if not self._policy.can_see(actor, booking.artist_id):
            raise PermissionDeniedError("You cannot see the payments of this booking.")

        return self._payments.list_for_booking(booking_id)
