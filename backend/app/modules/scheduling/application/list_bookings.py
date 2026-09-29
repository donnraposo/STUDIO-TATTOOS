from datetime import datetime

from psycopg.types.range import Range

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository
from app.modules.scheduling.infrastructure.models.booking import Booking
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ListBookings:
    """Lista agendamentos conforme o alcance de quem pergunta.

    Gestor vê a agenda do estúdio; artista vê apenas a própria. O recorte está
    na consulta, então a agenda alheia nunca chega a ser lida.

    **A janela de tempo é o que torna a tela de agenda viável.** Sem ela, abrir
    um único dia traria o histórico inteiro do estúdio, e o custo cresceria toda
    semana até a tela ficar lenta sem ninguém ter mudado nada. O intervalo é
    opcional porque consultar histórico continua sendo um uso legítimo."""

    def __init__(self, bookings: BookingRepository, policy: SchedulingPolicy) -> None:
        self._bookings = bookings
        self._policy = policy

    def execute(
        self,
        actor: AuthenticatedUser,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
    ) -> list[Booking]:
        if not (actor.is_staff or actor.tattoos):
            raise PermissionDeniedError("You cannot list bookings.")

        window = self._build_window(starts_at, ends_at)

        if actor.is_staff:
            return self._bookings.list_all(window)
        return self._bookings.list_for_artist(actor.id, window)

    @staticmethod
    def _build_window(starts_at: datetime | None, ends_at: datetime | None) -> Range | None:
        """Exige os dois extremos ou nenhum.

        Meia janela seria uma armadilha silenciosa: quem informasse apenas o
        início receberia todo o futuro e leria isso como "o dia", descobrindo o
        engano só quando a agenda tivesse volume."""
        if starts_at is None and ends_at is None:
            return None

        if starts_at is None or ends_at is None:
            raise BusinessRuleError("Provide both ends of the period, or neither.")

        if ends_at <= starts_at:
            raise BusinessRuleError("The end of the period must be after its start.")

        return Range(starts_at, ends_at, bounds="[)")
