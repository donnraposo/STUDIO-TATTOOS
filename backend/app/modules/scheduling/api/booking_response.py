import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.scheduling.infrastructure.models.booking import Booking


class BookingResponse(BaseModel):
    """Agendamento devolvido ao cliente.

    O `tstzrange` do banco é aberto em início e fim, porque um intervalo é mais
    difícil de consumir na interface do que dois instantes."""

    id: uuid.UUID
    client_id: uuid.UUID
    artist_id: uuid.UUID
    bench_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    #: O trabalho orcado que este horario atende, quando ha um. Nulo no
    #: agendamento de guest, que nao acessa orcamentos (RN-ORC-001).
    quote_id: uuid.UUID | None
    #: O sinal informado ao marcar. Nulo usa o padrao do estudio; e o valor que
    #: chega preenchido no registro do pagamento, onde o gestor pode corrigi-lo.
    deposit_amount: Decimal | None
    requested_at: datetime
    rejection_reason: str | None
    rejection_note: str | None

    @classmethod
    def from_model(cls, booking: Booking) -> "BookingResponse":
        return cls(
            id=booking.id,
            client_id=booking.client_id,
            artist_id=booking.artist_id,
            bench_id=booking.bench_id,
            starts_at=booking.period.lower,
            ends_at=booking.period.upper,
            status=str(booking.status),
            quote_id=booking.quote_id,
            deposit_amount=booking.deposit_amount,
            requested_at=booking.requested_at,
            rejection_reason=booking.rejection_reason,
            rejection_note=booking.rejection_note,
        )
