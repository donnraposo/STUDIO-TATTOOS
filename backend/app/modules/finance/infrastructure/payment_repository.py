import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.domain.payment_kind import PaymentKind
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.infrastructure.models.payment import Payment


class PaymentRepository:
    """Acesso aos pagamentos."""

    _LIVE = (PaymentStatus.REPORTED, PaymentStatus.CONFIRMED)

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, payment: Payment) -> Payment:
        self._session.add(payment)
        self._session.flush()
        return payment

    def find_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        return self._session.get(Payment, payment_id)

    def list_for_booking(self, booking_id: uuid.UUID) -> list[Payment]:
        statement = (
            select(Payment)
            .where(Payment.booking_id == booking_id)
            .order_by(Payment.reported_at)
        )
        return list(self._session.execute(statement).scalars())

    def list_for_session(self, session_id: uuid.UUID) -> list[Payment]:
        statement = (
            select(Payment)
            .where(Payment.session_id == session_id)
            .order_by(Payment.reported_at)
        )
        return list(self._session.execute(statement).scalars())

    def list_by_status(self, status: PaymentStatus) -> list[Payment]:
        """Todos os pagamentos num estado, no estudio inteiro.

        E a consulta do painel do gestor (secao 10.1): o que esta aguardando
        confirmacao. Nao recebe recorte por artista porque quem confirma
        recebimento e sempre o gestor (RN-PAG-002), e ele ve tudo."""
        statement = (
            select(Payment).where(Payment.status == status).order_by(Payment.reported_at)
        )
        return list(self._session.execute(statement).scalars())

    def find_live_deposit(self, booking_id: uuid.UUID) -> Payment | None:
        """O sinal que ainda vale para este agendamento.

        Retido fica de fora: depois de uma remarcacao fora do prazo o cliente
        perde o sinal e precisa pagar outro (RN-AGE-008). Recusado tambem, pelo
        mesmo motivo -- e o que o indice parcial `uq_payment_live_deposit`
        garante do lado do banco."""
        statement = select(Payment).where(
            Payment.booking_id == booking_id,
            Payment.kind == PaymentKind.DEPOSIT,
            Payment.retained_at.is_(None),
            Payment.status.in_(PaymentRepository._LIVE),
        )
        return self._session.execute(statement).scalars().first()
