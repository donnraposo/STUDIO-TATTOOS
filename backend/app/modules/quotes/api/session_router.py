import uuid

from fastapi import APIRouter, Request, status

from app.core.container import Container
from app.modules.identity.api.session_authenticator import SessionAuthenticator
from app.modules.quotes.api.adjust_sessions_request import AdjustSessionsRequest
from app.modules.quotes.api.confirm_session_payment_request import ConfirmSessionPaymentRequest
from app.modules.quotes.api.mark_session_performed_request import MarkSessionPerformedRequest
from app.modules.quotes.api.session_response import SessionResponse


class SessionRouter:
    """Sessões de tatuagem (RN-ORC-005 e RN-ORC-006).

    As sessões **não** têm rota de criação. Elas nascem da aprovação do
    orçamento, na mesma transação, e oferecer um `POST /sessions` permitiria
    criar sessão sem orçamento aprovado — exatamente o estado que a RN-ORC-005
    impede ao exigir que só sessão concluída entre em repasse.

    A listagem pende do orçamento, `/quotes/{id}/sessions`, porque a sessão não
    existe fora dele. Marcar e confirmar pendem da sessão, porque quem age já
    tem a sessão em mão."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._authenticator = SessionAuthenticator(container)

    def build(self) -> APIRouter:
        router = APIRouter(tags=["sessions"])
        router.add_api_route(
            "/quotes/{quote_id}/sessions",
            self.list_sessions,
            methods=["GET"],
            response_model=list[SessionResponse],
        )
        router.add_api_route(
            "/quotes/{quote_id}/sessions/adjust",
            self.adjust_sessions,
            methods=["POST"],
            response_model=list[SessionResponse],
        )
        router.add_api_route(
            "/sessions/{session_id}/mark-done",
            self.mark_done,
            methods=["POST"],
            response_model=SessionResponse,
            status_code=status.HTTP_200_OK,
        )
        router.add_api_route(
            "/sessions/{session_id}/confirm-payment",
            self.confirm_payment,
            methods=["POST"],
            response_model=SessionResponse,
        )
        return router

    def list_sessions(self, quote_id: uuid.UUID, request: Request) -> list[SessionResponse]:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            records = self._container.quotes.list_sessions(session).execute(actor, quote_id)
            return [SessionResponse.from_model(record) for record in records]

    def adjust_sessions(
        self, quote_id: uuid.UUID, payload: AdjustSessionsRequest, request: Request
    ) -> list[SessionResponse]:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            records = self._container.quotes.adjust_remaining_sessions(session).execute(
                actor=actor, quote_id=quote_id, planned_values=payload.planned_values
            )
            return [SessionResponse.from_model(record) for record in records]

    def mark_done(
        self, session_id: uuid.UUID, payload: MarkSessionPerformedRequest, request: Request
    ) -> SessionResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            record = self._container.quotes.mark_session_performed(session).execute(
                actor=actor,
                session_id=session_id,
                performed_at=payload.performed_at,
                charged_value=payload.charged_value,
            )
            return SessionResponse.from_model(record)

    def confirm_payment(
        self, session_id: uuid.UUID, payload: ConfirmSessionPaymentRequest, request: Request
    ) -> SessionResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            record = self._container.quotes.confirm_session_payment(session).execute(
                actor=actor,
                session_id=session_id,
                charged_value=payload.charged_value,
                reason=payload.reason,
            )
            return SessionResponse.from_model(record)
