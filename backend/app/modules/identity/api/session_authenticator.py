import uuid

from fastapi import HTTPException, Request, status

from app.core.container import Container
from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class SessionAuthenticator:
    """Resolve a identidade a partir do cookie de sessao.

    Existe como peca propria para que todo modulo autentique da mesma forma —
    autorizacao duplicada em cada rota e como brechas aparecem."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._cookie_name = container.settings.session_cookie_name

    def require_user(self, request: Request) -> AuthenticatedUser:
        session_id = self.read_session_id(request)
        if session_id is None:
            raise self._unauthenticated()

        with self._container.database.session() as session:
            user = self._container.identity.resolve_session(session).execute(session_id)

        if user is None:
            raise self._unauthenticated()
        return user

    def read_session_id(self, request: Request) -> uuid.UUID | None:
        raw = request.cookies.get(self._cookie_name)
        if not raw:
            return None
        try:
            return uuid.UUID(raw)
        except ValueError:
            return None

    @staticmethod
    def _unauthenticated() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated."
        )
