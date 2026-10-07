import uuid
from datetime import datetime

from pydantic import BaseModel


class BookingRequest(BaseModel):
    """Solicitação de agendamento.

    `artist_id` só é aceito de gestor agendando para outra pessoa; o artista
    agendando para si pode omitir. `approve_immediately` atende à RN-AGE-005,
    que permite ao gestor criar já aprovado.

    `quote_id` liga o horário ao trabalho orçado que ele atende. É opcional
    porque o guest não acessa orçamentos (RN-ORC-001) e agenda para clientes
    próprios sem nenhum."""

    client_id: uuid.UUID
    bench_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    artist_id: uuid.UUID | None = None
    approve_immediately: bool = False
    quote_id: uuid.UUID | None = None
