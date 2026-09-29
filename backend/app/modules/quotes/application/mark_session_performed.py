import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.session_policy import SessionPolicy
from app.modules.quotes.domain.session_status import SessionStatus
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.quotes.infrastructure.tattoo_session_repository import TattooSessionRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class MarkSessionPerformed:
    """O artista registra que a sessão aconteceu (RN-ORC-005 e RN-ORC-006).

    **Valor ausente significa sessão inteira.** A RN-ORC-006 só pede o valor
    quando a sessão foi interrompida, e é dela que nasce o `PARTIALLY_DONE`:
    informar quanto foi efetivamente cobrado é o que distingue uma sessão
    interrompida de uma sessão completa. Um parâmetro booleano separado diria a
    mesma coisa duas vezes e abriria a chance de dizer as duas diferente.

    **Marcar não conclui.** A sessão fica `DONE` ou `PARTIALLY_DONE` e só entra
    em repasse depois de o gestor confirmar o recebimento (RN-ORC-005). A
    restrição `ck_tattoo_session_paid_off_requires_confirmation` garante isso no
    banco, mesmo que alguém remova esta classe.

    **Remarcar é correção, e correção é permitida.** A regra manda registrar
    correções posteriores com data, hora e responsável, e a auditoria guarda o
    estado anterior. O que não se corrige por aqui é sessão já quitada: desfazer
    uma confirmação de recebimento é ato do gestor, não do artista."""

    _CORRECTABLE = (SessionStatus.SCHEDULED, SessionStatus.DONE, SessionStatus.PARTIALLY_DONE)

    def __init__(
        self,
        sessions: TattooSessionRepository,
        quotes: QuoteRepository,
        policy: SessionPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._sessions = sessions
        self._quotes = quotes
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        session_id: uuid.UUID,
        performed_at: datetime | None = None,
        charged_value: Decimal | None = None,
    ) -> TattooSession:
        record = self._sessions.find_by_id(session_id)
        if record is None:
            raise BusinessRuleError("Session not found.")

        quote = self._quotes.find_by_id(record.quote_id)
        if quote is None:
            raise BusinessRuleError("Session not found.")

        if not self._policy.can_mark_performed(actor, quote.artist_id):
            raise PermissionDeniedError("You cannot mark this session as performed.")

        if record.status not in self._CORRECTABLE:
            raise BusinessRuleError("This session can no longer be marked as performed.")

        self._ensure_partial_is_partial(record, charged_value)

        previous = self._snapshot(record)
        record.status = (
            SessionStatus.DONE if charged_value is None else SessionStatus.PARTIALLY_DONE
        )
        record.charged_value = charged_value
        record.performed_at = performed_at or datetime.now(UTC)
        record.marked_done_by = actor.id
        self._sessions.persist(record)

        self._audit.record(
            actor_id=actor.id,
            action="SESSION_MARKED_PERFORMED",
            module="quotes",
            entity_type="tattoo_session",
            entity_id=str(record.id),
            old_values=previous,
            new_values=self._snapshot(record),
        )
        return record

    @staticmethod
    def _ensure_partial_is_partial(record: TattooSession, charged_value: Decimal | None) -> None:
        """Parcial cobra menos do que o previsto — senão não foi parcial.

        Aceitar um valor igual ao previsto marcaria como interrompida uma sessão
        que correu inteira, e o repasse sairia certo por acaso enquanto o
        histórico contaria outra história."""
        if charged_value is None:
            return
        if charged_value < 0:
            raise BusinessRuleError("The charged value cannot be negative.")
        if charged_value >= record.planned_value:
            raise BusinessRuleError(
                "A partial session must be charged less than the planned value."
                " Omit the value when the session ran in full."
            )

    @staticmethod
    def _snapshot(record: TattooSession) -> dict[str, object]:
        return {
            "status": str(record.status),
            "charged_value": str(record.charged_value)
            if record.charged_value is not None
            else None,
            "performed_at": record.performed_at.isoformat()
            if record.performed_at is not None
            else None,
        }
