import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.session_repository import SessionRepository
from app.modules.identity.infrastructure.user_repository import UserRepository


class ResolveSession:
    """Traduz o identificador do cookie em um usuario autenticado.

    Reconfere o estado da conta a cada requisicao: uma conta bloqueada perde o
    acesso imediatamente, mesmo que a sessao ainda esteja dentro do prazo
    (RN 2.5). Cada uso valido desloca a janela de inatividade."""

    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        idle_minutes: int,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._idle_minutes = idle_minutes

    def execute(self, session_id: uuid.UUID) -> AuthenticatedUser | None:
        record = self._sessions.find_valid(session_id)
        if record is None:
            return None

        account = self._users.find_by_id(record.user_id)
        if account is None or account.status != UserStatus.ACTIVE:
            return None

        self._sessions.extend_idle_window(record, self._idle_minutes)

        return AuthenticatedUser(
            id=account.id,
            email=account.email,
            full_name=account.full_name,
            role=UserRole(account.role),
            acts_as_artist=account.acts_as_artist,
        )
