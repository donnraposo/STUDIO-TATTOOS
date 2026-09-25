import uuid

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.container import Container
from app.core.csrf_guard import CsrfGuard
from app.modules.identity.api.current_user_response import CurrentUserResponse
from app.modules.identity.api.login_request import LoginRequest
from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class AuthRouter:
    """Login, logout e identidade corrente.

    O navegador recebe dois cookies: o da sessao, `HttpOnly`, que o script nao
    le; e o do CSRF, legivel, que precisa voltar no cabecalho das operacoes que
    alteram dados."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._settings = container.settings

    def build(self) -> APIRouter:
        router = APIRouter(prefix="/auth", tags=["auth"])
        router.add_api_route("/login", self.login, methods=["POST"])
        router.add_api_route("/logout", self.logout, methods=["POST"])
        router.add_api_route(
            "/me", self.current_user, methods=["GET"], response_model=CurrentUserResponse
        )
        return router

    def login(self, payload: LoginRequest, request: Request, response: Response) -> dict[str, str]:
        with self._container.database.session() as session:
            use_case = self._container.identity.authenticate_user(session)
            session_id = use_case.execute(
                email=payload.email,
                password=payload.password,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

        if session_id is None:
            # Mensagem unica de proposito: nao revela se o e-mail existe nem se a
            # conta esta bloqueada.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
            )

        self._attach_cookies(response, session_id)
        return {"status": "authenticated"}

    def logout(self, request: Request, response: Response) -> dict[str, str]:
        self._container.csrf_guard.validate(request)
        session_id = self._read_session_id(request)

        if session_id is not None:
            with self._container.database.session() as session:
                self._container.identity.end_session(session).execute(session_id)

        self._clear_cookies(response)
        return {"status": "signed out"}

    def current_user(self, request: Request) -> CurrentUserResponse:
        user = self._require_user(request)
        return CurrentUserResponse.from_domain(user)

    def _require_user(self, request: Request) -> AuthenticatedUser:
        session_id = self._read_session_id(request)
        if session_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated."
            )

        with self._container.database.session() as session:
            user = self._container.identity.resolve_session(session).execute(session_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated."
            )
        return user

    def _read_session_id(self, request: Request) -> uuid.UUID | None:
        raw = request.cookies.get(self._settings.session_cookie_name)
        if not raw:
            return None
        try:
            return uuid.UUID(raw)
        except ValueError:
            return None

    def _attach_cookies(self, response: Response, session_id: uuid.UUID) -> None:
        secure = self._settings.cookies_require_https
        response.set_cookie(
            key=self._settings.session_cookie_name,
            value=str(session_id),
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            key=self._settings.csrf_cookie_name,
            value=CsrfGuard.issue_token(),
            httponly=False,
            secure=secure,
            samesite="lax",
            path="/",
        )

    def _clear_cookies(self, response: Response) -> None:
        response.delete_cookie(self._settings.session_cookie_name, path="/")
        response.delete_cookie(self._settings.csrf_cookie_name, path="/")
