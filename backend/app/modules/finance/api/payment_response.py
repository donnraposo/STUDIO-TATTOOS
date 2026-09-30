import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.finance.infrastructure.models.payment import Payment


class PaymentResponse(BaseModel):
    """Pagamento devolvido ao cliente da API.

    `retained_at` aparece porque retido e devolvido nao sao a mesma coisa e a
    interface precisa dizer qual dos dois foi: o sinal retido continua
    confirmado -- o estudio ficou com ele (RN-AGE-009) --, e so um valor
    devolvido saiu do caixa (RN-PAG-009). Uma tela que mostrasse apenas o estado
    contaria a metade errada da historia."""

    id: uuid.UUID
    booking_id: uuid.UUID | None
    session_id: uuid.UUID | None
    client_id: uuid.UUID | None
    amount: Decimal
    kind: str
    method: str
    status: str
    note: str | None
    reported_at: datetime
    confirmed_at: datetime | None
    refused_at: datetime | None
    refusal_reason: str | None
    retained_at: datetime | None
    retained_reason: str | None

    @classmethod
    def from_model(cls, payment: Payment) -> "PaymentResponse":
        return cls(
            id=payment.id,
            booking_id=payment.booking_id,
            session_id=payment.session_id,
            client_id=payment.client_id,
            amount=payment.amount,
            kind=str(payment.kind),
            method=str(payment.method),
            status=str(payment.status),
            note=payment.note,
            reported_at=payment.reported_at,
            confirmed_at=payment.confirmed_at,
            refused_at=payment.refused_at,
            refusal_reason=payment.refusal_reason,
            retained_at=payment.retained_at,
            retained_reason=payment.retained_reason,
        )
