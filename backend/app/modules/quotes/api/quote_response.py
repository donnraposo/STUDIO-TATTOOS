import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.quotes.infrastructure.models.quote import Quote


class QuoteResponse(BaseModel):
    """Orçamento devolvido ao cliente da API.

    `artist_percentage` vem nulo enquanto pendente e preenchido depois da
    aprovação — é o que permite à interface mostrar o percentual acordado sem
    recalcular nada, e portanto sem risco de exibir um número diferente do que
    será pago."""

    id: uuid.UUID
    client_id: uuid.UUID
    artist_id: uuid.UUID
    origin: str
    description: str
    body_region: str
    size_estimate: str
    total_value: Decimal
    planned_sessions: int
    planned_value_per_session: Decimal
    estimated_duration_minutes: int
    notes: str | None
    status: str
    artist_percentage: Decimal | None
    approved_at: datetime | None
    rejection_reason: str | None
    rejection_note: str | None
    created_at: datetime

    @classmethod
    def from_model(cls, quote: Quote) -> "QuoteResponse":
        return cls(
            id=quote.id,
            client_id=quote.client_id,
            artist_id=quote.artist_id,
            origin=str(quote.origin),
            description=quote.description,
            body_region=quote.body_region,
            size_estimate=quote.size_estimate,
            total_value=quote.total_value,
            planned_sessions=quote.planned_sessions,
            planned_value_per_session=quote.planned_value_per_session,
            estimated_duration_minutes=quote.estimated_duration_minutes,
            notes=quote.notes,
            status=str(quote.status),
            artist_percentage=quote.artist_percentage,
            approved_at=quote.approved_at,
            rejection_reason=quote.rejection_reason,
            rejection_note=quote.rejection_note,
            created_at=quote.created_at,
        )
