import uuid

from fastapi import APIRouter, Request, status

from app.core.container import Container
from app.modules.identity.api.account_response import AccountResponse
from app.modules.identity.api.block_account_request import BlockAccountRequest
from app.modules.identity.api.create_account_request import CreateAccountRequest
from app.modules.identity.api.session_authenticator import SessionAuthenticator


class AccountRouter:
    """Gestao de contas pela area de gerenciamento (RN 2.1 a 2.6).

    A rota nao decide autorizacao nem traduz erro: a alcada e resolvida pela
    politica de dominio e os erros viram HTTP em `ErrorHandlers`."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._authenticator = SessionAuthenticator(container)

    def build(self) -> APIRouter:
        router = APIRouter(prefix="/users", tags=["users"])
        router.add_api_route(
            "", self.list_accounts, methods=["GET"], response_model=list[AccountResponse]
        )
        router.add_api_route(
            "",
            self.create_account,
            methods=["POST"],
            response_model=AccountResponse,
            status_code=status.HTTP_201_CREATED,
        )
        router.add_api_route("/{account_id}/block", self.block_account, methods=["POST"])
        router.add_api_route("/{account_id}/unblock", self.unblock_account, methods=["POST"])
        return router

    def list_accounts(self, request: Request) -> list[AccountResponse]:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            accounts = self._container.identity.list_accounts(session).execute(actor)
            return [AccountResponse.from_model(account) for account in accounts]

    def create_account(self, payload: CreateAccountRequest, request: Request) -> AccountResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)

        with self._container.database.session() as session:
            account = self._container.identity.create_account(session).execute(
                actor=actor,
                email=payload.email,
                password=payload.password,
                full_name=payload.full_name,
                phone=payload.phone,
                role=payload.role,
                acts_as_artist=payload.acts_as_artist,
                artist_name=payload.artist_name,
            )
            return AccountResponse.from_model(account)

    def block_account(
        self, account_id: uuid.UUID, payload: BlockAccountRequest, request: Request
    ) -> dict[str, int | str]:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)

        with self._container.database.session() as session:
            revoked = self._container.identity.block_account(session).execute(
                actor=actor, target_id=account_id, reason=payload.reason
            )
            return {"status": "blocked", "revoked_sessions": revoked}

    def unblock_account(self, account_id: uuid.UUID, request: Request) -> dict[str, str]:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)

        with self._container.database.session() as session:
            self._container.identity.unblock_account(session).execute(
                actor=actor, target_id=account_id
            )
            return {"status": "active"}
