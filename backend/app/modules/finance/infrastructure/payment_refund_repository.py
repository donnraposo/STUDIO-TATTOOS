import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.models.payment_refund import PaymentRefund


class PaymentRefundRepository:
    """Acesso as devolucoes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, refund: PaymentRefund) -> PaymentRefund:
        self._session.add(refund)
        self._session.flush()
        return refund

    def list_for_payment(self, payment_id: uuid.UUID) -> list[PaymentRefund]:
        statement = (
            select(PaymentRefund)
            .where(PaymentRefund.payment_id == payment_id)
            .order_by(PaymentRefund.refunded_at)
        )
        return list(self._session.execute(statement).scalars())
