import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.finance.infrastructure.models.payment_refund import PaymentRefund


class RefundResponse(BaseModel):
    """Devolucao devolvida ao cliente da API (RN-PAG-009)."""

    id: uuid.UUID
    payment_id: uuid.UUID
    amount: Decimal
    method: str
    reason: str
    note: str | None
    refunded_at: datetime

    @classmethod
    def from_model(cls, refund: PaymentRefund) -> "RefundResponse":
        return cls(
            id=refund.id,
            payment_id=refund.payment_id,
            amount=refund.amount,
            method=refund.method if isinstance(refund.method, str) else str(refund.method),
            reason=refund.reason,
            note=refund.note,
            refunded_at=refund.refunded_at,
        )
