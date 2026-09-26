from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.identity.application.authenticate_user import AuthenticateUser
from app.modules.identity.application.block_account import BlockAccount
from app.modules.identity.application.create_account import CreateAccount
from app.modules.identity.application.end_session import EndSession
from app.modules.identity.application.list_accounts import ListAccounts
from app.modules.identity.application.resolve_session import ResolveSession
from app.modules.identity.application.unblock_account import UnblockAccount
from app.modules.identity.domain.account_management_policy import AccountManagementPolicy
from app.modules.identity.infrastructure.password_hasher import PasswordHasher
from app.modules.identity.infrastructure.session_repository import SessionRepository
from app.modules.identity.infrastructure.status_history_repository import (
    StatusHistoryRepository,
)
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder


class IdentityFactory:
    """Monta os casos de uso do modulo a partir de uma sessao de banco.

    Existe uma fabrica por modulo para que o `Container` nao precise conhecer o
    interior de cada dominio conforme o sistema cresce."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._hasher = PasswordHasher()
        self._policy = AccountManagementPolicy()

    @property
    def password_hasher(self) -> PasswordHasher:
        return self._hasher

    @property
    def policy(self) -> AccountManagementPolicy:
        return self._policy

    def users(self, session: Session) -> UserRepository:
        return UserRepository(session)

    def sessions(self, session: Session) -> SessionRepository:
        return SessionRepository(session)

    def status_history(self, session: Session) -> StatusHistoryRepository:
        return StatusHistoryRepository(session)

    def audit(self, session: Session) -> AuditRecorder:
        return AuditRecorder(session)

    def authenticate_user(self, session: Session) -> AuthenticateUser:
        return AuthenticateUser(
            users=self.users(session),
            sessions=self.sessions(session),
            hasher=self._hasher,
            idle_minutes=self._settings.session_idle_minutes,
            absolute_hours=self._settings.session_absolute_hours,
        )

    def resolve_session(self, session: Session) -> ResolveSession:
        return ResolveSession(
            users=self.users(session),
            sessions=self.sessions(session),
            idle_minutes=self._settings.session_idle_minutes,
        )

    def end_session(self, session: Session) -> EndSession:
        return EndSession(sessions=self.sessions(session))

    def create_account(self, session: Session) -> CreateAccount:
        return CreateAccount(
            users=self.users(session),
            hasher=self._hasher,
            policy=self._policy,
            audit=self.audit(session),
        )

    def block_account(self, session: Session) -> BlockAccount:
        return BlockAccount(
            users=self.users(session),
            sessions=self.sessions(session),
            history=self.status_history(session),
            policy=self._policy,
            audit=self.audit(session),
        )

    def unblock_account(self, session: Session) -> UnblockAccount:
        return UnblockAccount(
            users=self.users(session),
            history=self.status_history(session),
            policy=self._policy,
            audit=self.audit(session),
        )

    def list_accounts(self, session: Session) -> ListAccounts:
        return ListAccounts(users=self.users(session), policy=self._policy)
