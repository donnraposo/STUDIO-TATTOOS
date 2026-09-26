from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository
from app.modules.scheduling.infrastructure.models.booking import Booking
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ListBookings:
    """Lista agendamentos conforme o alcance de quem pergunta.

    Gestor vê a agenda do estúdio; artista vê apenas a própria. O recorte está
    na consulta, então a agenda alheia nunca chega a ser lida."""

    def __init__(self, bookings: BookingRepository, policy: SchedulingPolicy) -> None:
        self._bookings = bookings
        self._policy = policy

    def execute(self, actor: AuthenticatedUser) -> list[Booking]:
        if actor.is_staff:
            return self._bookings.list_all()
        if actor.tattoos:
            return self._bookings.list_for_artist(actor.id)
        raise PermissionDeniedError("You cannot list bookings.")
