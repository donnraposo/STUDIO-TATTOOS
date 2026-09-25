import uuid
from contextlib import suppress

from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.password_hasher import PasswordHasher
from app.modules.identity.infrastructure.session_repository import SessionRepository
from app.modules.identity.infrastructure.user_repository import UserRepository


class AuthenticateUser:
    """Verifica credenciais e abre uma sessao.

    Nao revela se um e-mail existe: credencial invalida e conta inexistente
    produzem o mesmo resultado nulo, conforme DOCS/04_ARQUITETURA_TECNICA.md
    secao 6. Por isso a verificacao do hash roda mesmo sem conta encontrada,
    evitando que o tempo de resposta denuncie a diferenca."""

    _DUMMY_HASH = (
        "$argon2id$v=19$m=65536,t=3,p=4$"
        "c29tZXNhbHRzb21lc2FsdA$8pVBlP3VCJmO0Qf6Jb8mUfwP5eZKqF0hXk4g5Xr4YvQ"
    )

    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        hasher: PasswordHasher,
        idle_minutes: int,
        absolute_hours: int,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._hasher = hasher
        self._idle_minutes = idle_minutes
        self._absolute_hours = absolute_hours

    def execute(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> uuid.UUID | None:
        account = self._users.find_by_email(email)

        if account is None:
            self._consume_comparable_time(password)
            return None

        if not self._hasher.verify(password, account.password_hash):
            return None

        if account.status != UserStatus.ACTIVE:
            return None

        session = self._sessions.create(
            user_id=account.id,
            idle_minutes=self._idle_minutes,
            absolute_hours=self._absolute_hours,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return session.id

    def _consume_comparable_time(self, password: str) -> None:
        # O hash sintetico pode ser recusado pelo verificador; o que importa aqui
        # e gastar o mesmo tempo de uma verificacao real.
        with suppress(Exception):
            self._hasher.verify(password, self._DUMMY_HASH)
