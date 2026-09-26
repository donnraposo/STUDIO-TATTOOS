import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class SchedulingPolicy:
    """Quem pode o quê na agenda (RN-AGE-005).

    A assimetria central: residente e guest **solicitam**; apenas proprietário e
    gerente **decidem**. Quando o gestor também tatua, pode aprovar o próprio
    agendamento — a alcada administrativa não se perde por ele atender."""

    def can_request(self, actor: AuthenticatedUser) -> bool:
        return actor.is_staff or actor.tattoos

    def can_decide(self, actor: AuthenticatedUser) -> bool:
        """Aprovar, rejeitar, remarcar e cancelar são decisões do estúdio."""
        return actor.is_staff

    def can_create_already_approved(self, actor: AuthenticatedUser) -> bool:
        """RN-AGE-005: o gestor pode criar já aprovado, desde que sem conflito."""
        return actor.is_staff

    def can_see_booking(
        self, actor: AuthenticatedUser, artist_id: uuid.UUID
    ) -> bool:
        if actor.is_staff:
            return True
        return actor.id == artist_id

    def can_manage_booths(self, actor: AuthenticatedUser) -> bool:
        """RN-AGE-011: acrescentar maca e bloquear horário são do gestor."""
        return actor.is_staff
