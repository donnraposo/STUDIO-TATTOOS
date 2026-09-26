from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.booth_repository import BoothRepository
from app.modules.scheduling.infrastructure.models.booth import Booth
from app.shared.errors.permission_denied_error import PermissionDeniedError


class CreateBooth:
    """Acrescenta uma maca (RN-AGE-001 e configuração operacional).

    A numeração é sequencial e atribuída pelo sistema: deixar o gestor escolher
    o número abriria espaço para duplicidade, e o número identifica a maca no
    dia a dia do estúdio."""

    def __init__(
        self,
        booths: BoothRepository,
        policy: SchedulingPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._booths = booths
        self._policy = policy
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, label: str | None = None) -> Booth:
        if not self._policy.can_manage_booths(actor):
            raise PermissionDeniedError("Only the studio management can add booths.")

        booth = self._booths.add(
            Booth(number=self._booths.next_number(), label=label.strip() if label else None)
        )

        self._audit.record(
            actor_id=actor.id,
            action="BOOTH_CREATED",
            module="scheduling",
            entity_type="booth",
            entity_id=str(booth.id),
            new_values={"number": booth.number},
        )
        return booth
