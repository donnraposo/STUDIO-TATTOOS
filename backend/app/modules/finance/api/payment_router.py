import uuid

from fastapi import APIRouter, Request, status

from app.core.container import Container
from app.modules.finance.api.payment_response import PaymentResponse
from app.modules.finance.api.refund_payment_request import RefundPaymentRequest
from app.modules.finance.api.refund_response import RefundResponse
from app.modules.finance.api.refuse_payment_request import RefusePaymentRequest
from app.modules.finance.api.register_payment_request import RegisterPaymentRequest
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.identity.api.session_authenticator import SessionAuthenticator


class PaymentRouter:
    """Pagamentos e devoluções (RN-PAG-001 a RN-PAG-009).

    Confirmar, recusar e devolver são ações próprias, e não um `PATCH` mudando o
    campo `status`. Cada uma registra coisas diferentes — quem confirmou, o
    motivo da recusa, a forma da devolução — e nenhuma delas é "editar um
    campo". Um `PATCH` genérico também permitiria o caminho que a RN-PAG-007
    proíbe: voltar um recusado a confirmado, apagando a recusa do histórico.

    **Não existe rota de exclusão.** A regra é explícita: um pagamento nunca
    será apagado. Correção entra como devolução vinculada ao lançamento
    original."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._authenticator = SessionAuthenticator(container)

    def build(self) -> APIRouter:
        router = APIRouter(tags=["payments"])
        router.add_api_route(
            "/payments",
            self.register_payment,
            methods=["POST"],
            response_model=PaymentResponse,
            status_code=status.HTTP_201_CREATED,
        )
        router.add_api_route(
            "/payments",
            self.list_by_status,
            methods=["GET"],
            response_model=list[PaymentResponse],
        )
        router.add_api_route(
            "/bookings/{booking_id}/payments",
            self.list_payments,
            methods=["GET"],
            response_model=list[PaymentResponse],
        )
        router.add_api_route(
            "/payments/{payment_id}/confirm",
            self.confirm_payment,
            methods=["POST"],
            response_model=PaymentResponse,
        )
        router.add_api_route(
            "/payments/{payment_id}/refuse",
            self.refuse_payment,
            methods=["POST"],
            response_model=PaymentResponse,
        )
        router.add_api_route(
            "/payments/{payment_id}/refund",
            self.refund_payment,
            methods=["POST"],
            response_model=RefundResponse,
            status_code=status.HTTP_201_CREATED,
        )
        return router

    def register_payment(
        self, payload: RegisterPaymentRequest, request: Request
    ) -> PaymentResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            payment = self._container.finance.register_payment(session).execute(
                actor=actor,
                amount=payload.amount,
                kind=payload.kind,
                method=payload.method,
                booking_id=payload.booking_id,
                session_id=payload.session_id,
                client_id=payload.client_id,
                note=payload.note,
            )
            return PaymentResponse.from_model(payment)

    def list_by_status(
        self, request: Request, status: PaymentStatus = PaymentStatus.REPORTED
    ) -> list[PaymentResponse]:
        """O padrão é `REPORTED` porque é a pergunta que o painel faz: o que
        está aguardando confirmação (seção 10.1)."""
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            payments = self._container.finance.list_payments_by_status(session).execute(
                actor, status
            )
            return [PaymentResponse.from_model(payment) for payment in payments]

    def list_payments(self, booking_id: uuid.UUID, request: Request) -> list[PaymentResponse]:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            payments = self._container.finance.list_payments(session).execute(actor, booking_id)
            return [PaymentResponse.from_model(payment) for payment in payments]

    def confirm_payment(self, payment_id: uuid.UUID, request: Request) -> PaymentResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            payment = self._container.finance.confirm_payment(session).execute(actor, payment_id)
            return PaymentResponse.from_model(payment)

    def refuse_payment(
        self, payment_id: uuid.UUID, payload: RefusePaymentRequest, request: Request
    ) -> PaymentResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            payment = self._container.finance.refuse_payment(session).execute(
                actor=actor, payment_id=payment_id, reason=payload.reason
            )
            return PaymentResponse.from_model(payment)

    def refund_payment(
        self, payment_id: uuid.UUID, payload: RefundPaymentRequest, request: Request
    ) -> RefundResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            refund = self._container.finance.refund_payment(session).execute(
                actor=actor,
                payment_id=payment_id,
                amount=payload.amount,
                method=payload.method,
                reason=payload.reason,
                note=payload.note,
            )
            return RefundResponse.from_model(refund)
