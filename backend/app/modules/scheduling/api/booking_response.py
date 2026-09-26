import uuid
from datetime import datetime

from pydantic import BaseModel

from app.modules.scheduling.infrastructure.models.booking import Booking


class BookingResponse(BaseModel):
    """Agendamento devolvido ao cliente.

    O `tstzrange` do banco é aberto em início e fim, porque um intervalo é mais
    difícil de consumir na interface do que dois instantes."""

    id: uuid.UUID
    client_id: uuid.UUID
    artist_id: uuid.UUID
    booth_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    requested_at: datetime
    rejection_reason: str | None
    rejection_note: str | None

    @classmethod
    def from_model(cls, booking: Booking) -> "BookingResponse":
        return cls(
            id=booking.id,
            client_id=booking.client_id,
            artist_id=booking.artist_id,
            booth_id=booking.booth_id,
            starts_at=booking.period.lower,
            ends_at=booking.period.upper,
            status=str(booking.status),
            requested_at=booking.requested_at,
            rejection_reason=booking.rejection_reason,
            rejection_note=booking.rejection_note,
        )
