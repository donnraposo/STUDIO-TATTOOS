from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.identity.application.authenticate_user import AuthenticateUser
from app.modules.identity.application.end_session import EndSession
from app.modules.identity.application.resolve_session import ResolveSession
from app.modules.identity.infrastructure.password_hasher import PasswordHasher
from app.modules.identity.infrastructure.session_repository import SessionRepository
from app.modules.identity.infrastructure.user_repository import UserRepository


class IdentityFactory:
    """Monta os casos de uso do modulo a partir de uma sessao de banco.

    Existe uma fabrica por modulo para que o `Container` nao precise conhecer o
    interior de cada dominio conforme o sistema cresce."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._hasher = PasswordHasher()

    @property
    def password_hasher(self) -> PasswordHasher:
        return self._hasher

    def users(self, session: Session) -> UserRepository:
        return UserRepository(session)

    def sessions(self, session: Session) -> SessionRepository:
        return SessionRepository(session)

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
