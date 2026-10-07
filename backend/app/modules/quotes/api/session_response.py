import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession


class SessionResponse(BaseModel):
    """Sessão devolvida ao cliente da API.

    `origin` e `artist_percentage` aparecem aqui embora também estejam no
    orçamento, e não é repetição por descuido: são a **cópia congelada** do
    acordo no momento da aprovação (RN-REP-006). O orçamento pode ter voltado a
    pendente e sido reaprovado com outro percentual desde então, e é o valor
    desta linha que o repasse vai usar.

    `charged_value` vem nulo enquanto a sessão está agendada ou foi realizada
    por inteiro sem confirmação. Preenchido, é o que realmente entrou — a base
    do repasse numa sessão parcial (RN-ORC-006)."""

    id: uuid.UUID
    quote_id: uuid.UUID
    sequence_number: int
    status: str
    origin: str
    planned_value: Decimal
    charged_value: Decimal | None
    artist_percentage: Decimal
    performed_at: datetime | None
    marked_done_by: uuid.UUID | None
    confirmed_at: datetime | None
    confirmed_by: uuid.UUID | None
    created_at: datetime

    @classmethod
    def from_model(cls, record: TattooSession) -> "SessionResponse":
        return cls(
            id=record.id,
            quote_id=record.quote_id,
            sequence_number=record.sequence_number,
            status=str(record.status),
            origin=str(record.origin),
            planned_value=record.planned_value,
            charged_value=record.charged_value,
            artist_percentage=record.artist_percentage,
            performed_at=record.performed_at,
            marked_done_by=record.marked_done_by,
            confirmed_at=record.confirmed_at,
            confirmed_by=record.confirmed_by,
            created_at=record.created_at,
        )
