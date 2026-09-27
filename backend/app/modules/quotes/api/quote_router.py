import uuid
from typing import Annotated

from fastapi import APIRouter, File, Request, Response, UploadFile, status

from app.core.container import Container
from app.modules.identity.api.session_authenticator import SessionAuthenticator
from app.modules.quotes.api.approve_quote_request import ApproveQuoteRequest
from app.modules.quotes.api.quote_fields_request import QuoteFieldsRequest
from app.modules.quotes.api.quote_request import QuoteRequest
from app.modules.quotes.api.quote_response import QuoteResponse
from app.modules.quotes.api.reference_image_response import ReferenceImageResponse
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
        router.add_api_route(
            "/quotes/{quote_id}/reference-images",
            self.list_reference_images,
            methods=["GET"],
            response_model=list[ReferenceImageResponse],
        )
        router.add_api_route(
            "/quotes/{quote_id}/reference-images",
            self.attach_reference_image,
            methods=["POST"],
            response_model=ReferenceImageResponse,
            status_code=status.HTTP_201_CREATED,
        )
        router.add_api_route(
            "/quotes/{quote_id}/reference-images/{image_id}",
            self.remove_reference_image,
            methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT,
        )
        router.add_api_route(
            "/quotes/{quote_id}/reference-images/{image_id}/content",
            self.read_reference_image_content,
            methods=["GET"],
            response_class=Response,
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

    def list_reference_images(
        self, quote_id: uuid.UUID, request: Request
    ) -> list[ReferenceImageResponse]:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            images = self._container.quotes.list_reference_images(session).execute(actor, quote_id)
            return [
                ReferenceImageResponse.from_model(image, self._content_path(quote_id, image.id))
                for image in images
            ]

    async def attach_reference_image(
        self,
        quote_id: uuid.UUID,
        request: Request,
        file: Annotated[UploadFile, File()],
    ) -> ReferenceImageResponse:
        """Lê o arquivo **antes** de abrir a sessão de banco.

        O upload é entrada de rede e pode demorar; manter uma transação aberta
        enquanto se espera o cliente terminar de enviar prende conexão do pool
        sem nenhum ganho."""
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        content = await file.read()
        with self._container.database.session() as session:
            image = self._container.quotes.attach_reference_image(session).execute(
                actor=actor,
                quote_id=quote_id,
                content=content,
                content_type=file.content_type or "application/octet-stream",
            )
            return ReferenceImageResponse.from_model(
                image, self._content_path(quote_id, image.id)
            )

    def remove_reference_image(
        self, quote_id: uuid.UUID, image_id: uuid.UUID, request: Request
    ) -> None:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            self._container.quotes.remove_reference_image(session).execute(
                actor=actor, quote_id=quote_id, image_id=image_id
            )

    def read_reference_image_content(
        self, quote_id: uuid.UUID, image_id: uuid.UUID, request: Request
    ) -> Response:
        """Entrega a imagem conferindo a sessão, no lugar de uma URL assinada.

        `private, no-store` porque a resposta é dado pessoal: sem isso, um proxy
        compartilhado ou o cache do navegador guardaria a foto de um cliente onde
        a expiração da sessão não alcança."""
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            file = self._container.quotes.read_reference_image(session).execute(
                actor=actor, quote_id=quote_id, image_id=image_id
            )
            return Response(
                content=file.content,
                media_type=file.content_type,
                headers={"Cache-Control": "private, no-store"},
            )

    def _content_path(self, quote_id: uuid.UUID, image_id: uuid.UUID) -> str:
        prefix = self._container.settings.api_prefix
        return f"{prefix}/quotes/{quote_id}/reference-images/{image_id}/content"
