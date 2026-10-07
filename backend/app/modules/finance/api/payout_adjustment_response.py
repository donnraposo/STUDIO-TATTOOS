import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.finance.infrastructure.models.payout_adjustment import PayoutAdjustment


class PayoutAdjustmentResponse(BaseModel):
    """Um ajuste negativo no demonstrativo (RN-REP-005).

    `reason` nao e opcional por acaso: um desconto sem explicacao no repasse e a
    forma mais rapida de perder a confianca de quem recebe."""

    id: uuid.UUID
    related_payment_id: uuid.UUID
    amount: Decimal
    reason: str
    created_at: datetime

    @classmethod
    def from_model(cls, adjustment: PayoutAdjustment) -> "PayoutAdjustmentResponse":
        return cls(
            id=adjustment.id,
            related_payment_id=adjustment.related_payment_id,
            amount=adjustment.amount,
            reason=adjustment.reason,
            created_at=adjustment.created_at,
        )
