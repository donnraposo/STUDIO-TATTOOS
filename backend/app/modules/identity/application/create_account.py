from app.modules.identity.domain.account_management_policy import AccountManagementPolicy
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.password_hasher import PasswordHasher
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class CreateAccount:
    """Cria uma conta pela area de gerenciamento.

    Contas criadas por gestor ja nascem ativas (RN 2.6); o estado
    PENDING_APPROVAL pertence ao autocadastro, que fica na Fase 2."""

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        policy: AccountManagementPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        email: str,
        password: str,
        full_name: str,
        phone: str,
        role: UserRole,
        acts_as_artist: bool = False,
        artist_name: str | None = None,
    ) -> UserAccount:
        if not self._policy.can_create(actor, role):
            raise PermissionDeniedError("You cannot create an account with this role.")

        normalized_email = email.strip()
        if self._users.exists_with_email(normalized_email):
            raise BusinessRuleError("This email is already registered.")

        if self._requires_artist_name(role, acts_as_artist) and not artist_name:
            raise BusinessRuleError("An artist name is required for someone who tattoos.")

        account = UserAccount(
            email=normalized_email,
            password_hash=self._hasher.hash(password),
            full_name=full_name.strip(),
            artist_name=artist_name.strip() if artist_name else None,
            phone=phone.strip(),
            role=role,
            acts_as_artist=acts_as_artist,
            status=UserStatus.ACTIVE,
            created_by=actor.id,
        )
        self._users.add(account)

        self._audit.record(
            actor_id=actor.id,
            action="ACCOUNT_CREATED",
            module="identity",
            entity_type="user_account",
            entity_id=str(account.id),
            new_values={"email": normalized_email, "role": str(role)},
        )
        return account

    @staticmethod
    def _requires_artist_name(role: UserRole, acts_as_artist: bool) -> bool:
        return acts_as_artist or role in (UserRole.RESIDENT, UserRole.GUEST)
