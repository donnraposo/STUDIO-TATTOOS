from datetime import datetime

from pydantic import BaseModel


class ClosePayoutsRequest(BaseModel):
    """Qual semana fechar (RN-REP-004).

    `reference` e qualquer instante **dentro** da semana desejada, e nao a data
    do fechamento. Pedir a data exata da sexta obrigaria quem chama a calcular as
    20h no fuso do estudio -- justamente a conta que o `PayoutWeek` existe para
    centralizar, e errar nela por uma hora move pagamentos de uma semana para a
    outra."""

    reference: datetime
