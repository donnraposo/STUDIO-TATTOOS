import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.finance.infrastructure.models.payout import Payout


class PayoutResponse(BaseModel):
    """Repasse semanal devolvido ao cliente da API (RN-REP-004).

    `period_end` e a sexta as 20h `Europe/Dublin` em UTC. A interface formata no
    fuso do estudio, como faz com todo instante -- mostrar no fuso do navegador
    daria uma semana deslocada que parece certa."""

    id: uuid.UUID
    artist_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    gross_total: Decimal
    adjustments_total: Decimal
    net_total: Decimal
    status: str
    paid_at: datetime | None
    paid_by: uuid.UUID | None

    @classmethod
    def from_model(cls, payout: Payout) -> "PayoutResponse":
        return cls(
            id=payout.id,
            artist_id=payout.artist_id,
            period_start=payout.period_start,
            period_end=payout.period_end,
            gross_total=payout.gross_total,
            adjustments_total=payout.adjustments_total,
            net_total=payout.net_total,
            status=str(payout.status),
            paid_at=payout.paid_at,
            paid_by=payout.paid_by,
        )
