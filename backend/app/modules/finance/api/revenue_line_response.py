import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.finance.domain.revenue_line import RevenueLine


class RevenueLineResponse(BaseModel):
    """Um atendimento no detalhamento do mes (RN 10.4).

    Sem o nome do artista: a interface ja resolve identificador em nome na tela
    de repasses, com a lista de contas que ela consome de qualquer forma.
    Carregar o nome aqui faria o faturamento depender do modulo de identidade
    para dizer um numero.

    `settled_at` e quando o estudio reconheceu o dinheiro, em UTC. A interface
    formata no fuso do estudio, como faz com todo instante."""

    session_id: uuid.UUID
    artist_id: uuid.UUID
    settled_at: datetime
    value: Decimal
    percentage: Decimal
    artist_amount: Decimal
    studio_amount: Decimal
    transferred: bool

    @classmethod
    def from_line(cls, line: RevenueLine) -> "RevenueLineResponse":
        return cls(
            session_id=line.session_id,
            artist_id=line.artist_id,
            settled_at=line.settled_at,
            value=line.value,
            percentage=line.percentage,
            artist_amount=line.artist_amount,
            studio_amount=line.studio_amount,
            transferred=line.transferred,
        )
