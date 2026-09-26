from app.modules.identity.domain.account_management_policy import AccountManagementPolicy
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ListAccounts:
    """Lista as contas do estudio. Restrita a proprietario e gerente: artistas
    nao acessam dados de outros artistas (RN 2.3)."""

    def __init__(self, users: UserRepository, policy: AccountManagementPolicy) -> None:
        self._users = users
        self._policy = policy

    def execute(self, actor: AuthenticatedUser) -> list[UserAccount]:
        if not self._policy.can_list(actor):
            raise PermissionDeniedError("You cannot list accounts.")
        return self._users.list_all()
