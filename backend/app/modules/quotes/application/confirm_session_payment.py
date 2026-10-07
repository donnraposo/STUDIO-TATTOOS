import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.session_policy import SessionPolicy
from app.modules.quotes.domain.session_status import SessionStatus
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession
from app.modules.quotes.infrastructure.tattoo_session_repository import TattooSessionRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ConfirmSessionPayment:
    """O gestor confirma o valor recebido e a sessão fica concluída
    (RN-ORC-005 e RN-ORC-006).

    **É a metade que falta.** O artista diz que a sessão aconteceu; o gestor diz
    quanto entrou. Só depois das duas a sessão vale para repasse — é por isso
    que `DONE` e `PAID_OFF` são estados diferentes, e não um campo booleano
    pendurado no mesmo estado.

    **O valor confirmado prevalece sobre o informado, e a divergência exige
    motivo.** A RN-ORC-005 manda registrar correções posteriores com data, hora,
    motivo e responsável. Uma correção silenciosa de valor é a diferença entre
    um acerto e um desvio, e nenhuma das duas se distingue da outra sem o
    motivo escrito.

    **Este caso de uso é provisório no desenho, não no comportamento.** O
    recebimento ainda é lançado à mão, como a RN-PAG-006 permite nesta versão. A
    M5 traz o módulo de pagamentos, e a confirmação passará a se apoiar num
    pagamento confirmado em vez de num valor digitado aqui."""

    _PERFORMED = (SessionStatus.DONE, SessionStatus.PARTIALLY_DONE)

    def __init__(
        self,
        sessions: TattooSessionRepository,
        policy: SessionPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._sessions = sessions
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        session_id: uuid.UUID,
        charged_value: Decimal | None = None,
        reason: str | None = None,
    ) -> TattooSession:
        if not self._policy.can_confirm(actor):
            raise PermissionDeniedError("Only the studio management can confirm a session.")

        record = self._sessions.find_by_id(session_id)
        if record is None:
            raise BusinessRuleError("Session not found.")

        if record.status not in self._PERFORMED:
            raise BusinessRuleError("Only a performed session can be confirmed.")

        confirmed = self._resolve(record, charged_value, reason)

        previous = self._snapshot(record)
        record.status = SessionStatus.PAID_OFF
        record.charged_value = confirmed
        record.confirmed_at = datetime.now(UTC)
        record.confirmed_by = actor.id
        self._sessions.persist(record)

        self._audit.record(
            actor_id=actor.id,
            action="SESSION_PAYMENT_CONFIRMED",
            module="quotes",
            entity_type="tattoo_session",
            entity_id=str(record.id),
            old_values=previous,
            new_values=self._snapshot(record),
            reason=reason,
        )
        return record

    def _resolve(
        self, record: TattooSession, charged_value: Decimal | None, reason: str | None
    ) -> Decimal:
        """Omitido, vale o que já estava: o valor da parcial ou o previsto da
        sessão inteira. Informado e diferente, é correção e pede motivo."""
        reported = (
            record.charged_value if record.charged_value is not None else record.planned_value
        )
        if charged_value is None or charged_value == reported:
            return reported

        if charged_value < 0:
            raise BusinessRuleError("The charged value cannot be negative.")
        if reason is None or not reason.strip():
            raise BusinessRuleError(
                "Confirming a value different from the reported one requires a reason."
            )
        return charged_value

    @staticmethod
    def _snapshot(record: TattooSession) -> dict[str, object]:
        return {
            "status": str(record.status),
            "charged_value": str(record.charged_value)
            if record.charged_value is not None
            else None,
            "confirmed_at": record.confirmed_at.isoformat()
            if record.confirmed_at is not None
            else None,
        }
