from decimal import Decimal

from pydantic import BaseModel, Field


class ApproveQuoteRequest(BaseModel):
    """Aprovação do orçamento (RN-ORC-002 e RN-REP-006).

    `artist_percentage` é opcional e serve para o gestor corrigir o percentual
    deste atendimento, como a RN-CLI-003 permite. Omitido, vale o padrão da
    origem: 70% para cliente próprio, 50% para indicação do estúdio."""

    artist_percentage: Decimal | None = Field(
        default=None, gt=0, le=100, max_digits=5, decimal_places=2
    )
