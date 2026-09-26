import uuid

from fastapi import APIRouter, Request, status

from app.core.container import Container
from app.modules.identity.api.session_authenticator import SessionAuthenticator
from app.modules.quotes.api.approve_quote_request import ApproveQuoteRequest
from app.modules.quotes.api.quote_fields_request import QuoteFieldsRequest
from app.modules.quotes.api.quote_request import QuoteRequest
from app.modules.quotes.api.quote_response import QuoteResponse
from app.modules.quotes.api.reject_quote_request import RejectQuoteRequest


class QuoteRouter:
    """Orçamentos (RN-ORC-001 a RN-ORC-004 e RN-REP-006).

    Aprovar e rejeitar são ações próprias, e não um `PUT` mudando o campo
    `status`: a aprovação congela o percentual e registra quem decidiu, e isso
    não é a mesma coisa que editar um campo."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._authenticator = SessionAuthenticator(container)

    def build(self) -> APIRouter:
        router = APIRouter(tags=["quotes"])
        router.add_api_route(
            "/quotes", self.list_quotes, methods=["GET"], response_model=list[QuoteResponse]
        )
        router.add_api_route(
            "/quotes",
            self.create_quote,
            methods=["POST"],
            response_model=QuoteResponse,
            status_code=status.HTTP_201_CREATED,
        )
        router.add_api_route(
            "/quotes/{quote_id}", self.get_quote, methods=["GET"], response_model=QuoteResponse
        )
        router.add_api_route(
            "/quotes/{quote_id}",
            self.update_quote,
            methods=["PUT"],
            response_model=QuoteResponse,
        )
        router.add_api_route(
            "/quotes/{quote_id}/approve",
            self.approve_quote,
            methods=["POST"],
            response_model=QuoteResponse,
        )
        router.add_api_route(
            "/quotes/{quote_id}/reject",
            self.reject_quote,
            methods=["POST"],
            response_model=QuoteResponse,
        )
        return router

    def list_quotes(self, request: Request) -> list[QuoteResponse]:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            quotes = self._container.quotes.list_quotes(session).execute(actor)
            return [QuoteResponse.from_model(quote) for quote in quotes]

    def get_quote(self, quote_id: uuid.UUID, request: Request) -> QuoteResponse:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            quote = self._container.quotes.get_quote(session).execute(actor, quote_id)
            return QuoteResponse.from_model(quote)

    def create_quote(self, payload: QuoteRequest, request: Request) -> QuoteResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            quote = self._container.quotes.create_quote(session).execute(
                actor=actor,
                client_id=payload.client_id,
                details=payload.to_details(),
                artist_id=payload.artist_id,
            )
            return QuoteResponse.from_model(quote)

    def update_quote(
        self, quote_id: uuid.UUID, payload: QuoteFieldsRequest, request: Request
    ) -> QuoteResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            quote = self._container.quotes.update_quote(session).execute(
                actor=actor, quote_id=quote_id, details=payload.to_details()
            )
            return QuoteResponse.from_model(quote)

    def approve_quote(
        self, quote_id: uuid.UUID, payload: ApproveQuoteRequest, request: Request
    ) -> QuoteResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            quote = self._container.quotes.approve_quote(session).execute(
                actor=actor,
                quote_id=quote_id,
                artist_percentage=payload.artist_percentage,
            )
            return QuoteResponse.from_model(quote)

    def reject_quote(
        self, quote_id: uuid.UUID, payload: RejectQuoteRequest, request: Request
    ) -> QuoteResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            quote = self._container.quotes.reject_quote(session).execute(
                actor=actor,
                quote_id=quote_id,
                reason=payload.reason,
                note=payload.note,
            )
            return QuoteResponse.from_model(quote)
