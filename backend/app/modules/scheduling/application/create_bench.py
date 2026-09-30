from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.bench_repository import BenchRepository
from app.modules.scheduling.infrastructure.models.bench import Bench
from app.shared.errors.permission_denied_error import PermissionDeniedError


class CreateBench:
    """Acrescenta uma maca (RN-AGE-001 e configuração operacional).

    A numeração é sequencial e atribuída pelo sistema: deixar o gestor escolher
    o número abriria espaço para duplicidade, e o número identifica a maca no
    dia a dia do estúdio."""

    def __init__(
        self,
        benches: BenchRepository,
        policy: SchedulingPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._benches = benches
        self._policy = policy
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, label: str | None = None) -> Bench:
        if not self._policy.can_manage_benches(actor):
            raise PermissionDeniedError("Only the studio management can add benches.")

        bench = self._benches.add(
            Bench(number=self._benches.next_number(), label=label.strip() if label else None)
        )

        self._audit.record(
            actor_id=actor.id,
            action="BENCH_CREATED",
            module="scheduling",
            entity_type="bench",
            entity_id=str(bench.id),
            new_values={"number": bench.number},
        )
        return bench
