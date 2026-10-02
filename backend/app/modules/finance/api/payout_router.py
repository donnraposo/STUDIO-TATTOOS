import uuid

from fastapi import APIRouter, Request, status

from app.core.container import Container
from app.modules.finance.api.close_payouts_request import ClosePayoutsRequest
from app.modules.finance.api.confirm_payout_request import ConfirmPayoutRequest
from app.modules.finance.api.payout_response import PayoutResponse
from app.modules.finance.api.payout_statement_response import PayoutStatementResponse
from app.modules.identity.api.session_authenticator import SessionAuthenticator


class PayoutRouter:
    """Repasses semanais (RN-REP-003 a RN-REP-007).

    **Fechar a semana é `POST`, e não um `GET` que calcula de lado.** O cálculo
    sob demanda poderia tentar-se na própria listagem, e seria um erro: uma
    consulta que grava surpreende quem a chama, atravessa cache e não pode ser
    repetida à vontade. Aqui o ato é explícito, do gestor, e idempotente —
    fechar duas vezes devolve o mesmo fechamento.

    **Não existe rota de recálculo nem de exclusão.** Um repasse é fotografia da
    semana; a RN-REP-005 manda corrigir por ajuste negativo no repasse seguinte,
    e não reescrevendo o anterior."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._authenticator = SessionAuthenticator(container)

    def build(self) -> APIRouter:
        router = APIRouter(tags=["payouts"])
        router.add_api_route(
            "/payouts", self.list_payouts, methods=["GET"], response_model=list[PayoutResponse]
        )
        router.add_api_route(
            "/payouts/close",
            self.close_week,
            methods=["POST"],
            response_model=list[PayoutResponse],
            status_code=status.HTTP_200_OK,
        )
        router.add_api_route(
            "/payouts/{payout_id}",
            self.statement,
            methods=["GET"],
            response_model=PayoutStatementResponse,
        )
        router.add_api_route(
            "/payouts/{payout_id}/confirm-paid",
            self.confirm_paid,
            methods=["POST"],
            response_model=PayoutResponse,
        )
        return router

    def list_payouts(self, request: Request) -> list[PayoutResponse]:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            payouts = self._container.finance.list_payouts(session).execute(actor)
            return [PayoutResponse.from_model(payout) for payout in payouts]

    def close_week(
        self, payload: ClosePayoutsRequest, request: Request
    ) -> list[PayoutResponse]:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            payouts = self._container.finance.close_weekly_payouts(session).execute(
                actor, payload.reference
            )
            return [PayoutResponse.from_model(payout) for payout in payouts]

    def statement(self, payout_id: uuid.UUID, request: Request) -> PayoutStatementResponse:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            statement = self._container.finance.payout_statement(session).execute(
                actor, payout_id
            )
            return PayoutStatementResponse.from_statement(statement)

    def confirm_paid(
        self, payout_id: uuid.UUID, payload: ConfirmPayoutRequest, request: Request
    ) -> PayoutResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            payout = self._container.finance.confirm_payout_paid(session).execute(
                actor=actor,
                payout_id=payout_id,
                receipt_object_key=payload.receipt_object_key,
            )
            return PayoutResponse.from_model(payout)
