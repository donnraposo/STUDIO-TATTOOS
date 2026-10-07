import uuid

from fastapi import APIRouter, Request, status

from app.core.container import Container
from app.modules.identity.api.account_response import AccountResponse
from app.modules.identity.api.artist_percentage_request import ArtistPercentageRequest
from app.modules.identity.api.block_account_request import BlockAccountRequest
from app.modules.identity.api.create_account_request import CreateAccountRequest
from app.modules.identity.api.session_authenticator import SessionAuthenticator
from app.modules.identity.api.set_password_request import SetPasswordRequest
from app.modules.identity.api.update_account_request import UpdateAccountRequest


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
        router.add_api_route(
            "/{account_id}",
            self.update_account,
            methods=["PUT"],
            response_model=AccountResponse,
        )
        router.add_api_route(
            "/{account_id}/password",
            self.set_password,
            methods=["PUT"],
            response_model=AccountResponse,
        )
        router.add_api_route("/{account_id}/block", self.block_account, methods=["POST"])
        router.add_api_route("/{account_id}/unblock", self.unblock_account, methods=["POST"])
        router.add_api_route(
            "/{account_id}/percentage",
            self.set_percentage,
            methods=["PUT"],
            response_model=AccountResponse,
        )
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

    def update_account(
        self, account_id: uuid.UUID, payload: UpdateAccountRequest, request: Request
    ) -> AccountResponse:
        """`PUT` e não `PATCH`: o formulário manda o cadastro inteiro, e um campo
        ausente seria ambíguo entre "não mexa" e "apague"."""
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)

        with self._container.database.session() as session:
            account = self._container.identity.update_account(session).execute(
                actor=actor,
                account_id=account_id,
                email=payload.email,
                full_name=payload.full_name,
                phone=payload.phone,
                role=payload.role,
                acts_as_artist=payload.acts_as_artist,
                artist_name=payload.artist_name,
            )
            return AccountResponse.from_model(account)

    def set_password(
        self, account_id: uuid.UUID, payload: SetPasswordRequest, request: Request
    ) -> AccountResponse:
        """Rota propria e não campo do cadastro: trocar senha encerra as sessões
        da conta, e no meio de um `salvar` de telefone o gestor derrubaria
        alguém sem querer."""
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)

        with self._container.database.session() as session:
            account = self._container.identity.set_account_password(session).execute(
                actor=actor, account_id=account_id, password=payload.password
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

    def set_percentage(
        self, account_id: uuid.UUID, payload: ArtistPercentageRequest, request: Request
    ) -> AccountResponse:
        """`PUT` e não `PATCH`: o acordo é substituído por inteiro, e enviar
        nulo o encerra. Um `PATCH` deixaria ambíguo se o campo ausente significa
        "não mexa" ou "apague"."""
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            artist = self._container.identity.set_artist_percentage(session).execute(
                actor=actor, artist_id=account_id, percentage=payload.percentage
            )
            return AccountResponse.from_model(artist)
