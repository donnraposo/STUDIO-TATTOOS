import uuid

from app.modules.identity.domain.account_management_policy import AccountManagementPolicy
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.session_repository import SessionRepository
from app.modules.identity.infrastructure.status_history_repository import (
    StatusHistoryRepository,
)
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class BlockAccount:
    """Bloqueia uma conta e encerra suas sessoes na mesma transacao (RN 2.5).

    O bloqueio preserva historico, pagamentos e atendimentos. Agendamentos
    futuros nao sao cancelados: cabe ao gestor transferi-los ou cancela-los."""

    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        history: StatusHistoryRepository,
        policy: AccountManagementPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._history = history
        self._policy = policy
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, target_id: uuid.UUID, reason: str) -> int:
        account = self._users.find_by_id(target_id)
        if account is None:
            raise BusinessRuleError("Account not found.")

        target_role = UserRole(account.role)
        if not self._policy.can_change_status(actor, target_role):
            raise PermissionDeniedError("You cannot block this account.")

        if account.status == UserStatus.BLOCKED:
            raise BusinessRuleError("This account is already blocked.")

        self._guard_last_active_owner(account.id, target_role)

        previous = str(account.status)
        account.status = UserStatus.BLOCKED

        # Revogar na mesma transacao e o que torna o bloqueio imediato: se o
        # commit falhar, a conta continua ativa e as sessoes tambem.
        revoked = self._sessions.revoke_all_for_user(account.id)

        self._users.add(account)
        self._history.record(
            user_id=account.id,
            from_status=previous,
            to_status=str(UserStatus.BLOCKED),
            actor_id=actor.id,
            reason=reason,
        )
        self._audit.record(
            actor_id=actor.id,
            action="ACCOUNT_BLOCKED",
            module="identity",
            entity_type="user_account",
            entity_id=str(account.id),
            old_values={"status": previous},
            new_values={"status": str(UserStatus.BLOCKED), "revoked_sessions": revoked},
            reason=reason,
        )
        return revoked

    def _guard_last_active_owner(self, target_id: uuid.UUID, target_role: UserRole) -> None:
        """RN 2.5: o estudio nunca pode ficar sem administracao."""
        if target_role != UserRole.OWNER:
            return
        if self._users.count_active_owners(excluding=target_id) == 0:
            raise BusinessRuleError(
                "The last active owner cannot be blocked; the studio would be left "
                "without administration."
            )
