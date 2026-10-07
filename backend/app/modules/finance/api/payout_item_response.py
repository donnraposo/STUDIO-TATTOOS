import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.modules.finance.infrastructure.models.payout_item import PayoutItem


class PayoutItemResponse(BaseModel):
    """Uma sessao dentro do demonstrativo (RN-REP-007).

    Traz os tres numeros que a regra manda exibir -- valor recebido, percentual
    aplicado e o quanto coube ao artista -- para que ele possa refazer a conta
    sem pedir explicacao a ninguem."""

    id: uuid.UUID
    session_id: uuid.UUID
    received_amount: Decimal
    percentage: Decimal
    amount: Decimal

    @classmethod
    def from_model(cls, item: PayoutItem) -> "PayoutItemResponse":
        return cls(
            id=item.id,
            session_id=item.session_id,
            received_amount=item.received_amount,
            percentage=item.percentage,
            amount=item.amount,
        )
