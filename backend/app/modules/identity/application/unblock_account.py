import uuid

from app.modules.identity.domain.account_management_policy import AccountManagementPolicy
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.status_history_repository import (
    StatusHistoryRepository,
)
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class UnblockAccount:
    """Reativa uma conta bloqueada, seguindo a mesma hierarquia do bloqueio
    (RN 2.5). Sessoes antigas continuam revogadas: e preciso autenticar de novo."""

    def __init__(
        self,
        users: UserRepository,
        history: StatusHistoryRepository,
        policy: AccountManagementPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._users = users
        self._history = history
        self._policy = policy
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, target_id: uuid.UUID) -> None:
        account = self._users.find_by_id(target_id)
        if account is None:
            raise BusinessRuleError("Account not found.")

        if not self._policy.can_change_status(actor, UserRole(account.role)):
            raise PermissionDeniedError("You cannot reactivate this account.")

        if account.status != UserStatus.BLOCKED:
            raise BusinessRuleError("This account is not blocked.")

        previous = str(account.status)
        account.status = UserStatus.ACTIVE
        self._users.add(account)

        self._history.record(
            user_id=account.id,
            from_status=previous,
            to_status=str(UserStatus.ACTIVE),
            actor_id=actor.id,
        )
        self._audit.record(
            actor_id=actor.id,
            action="ACCOUNT_UNBLOCKED",
            module="identity",
            entity_type="user_account",
            entity_id=str(account.id),
            old_values={"status": previous},
            new_values={"status": str(UserStatus.ACTIVE)},
        )
