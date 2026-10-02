from dataclasses import dataclass

from app.modules.finance.infrastructure.models.payout import Payout
from app.modules.finance.infrastructure.models.payout_adjustment import PayoutAdjustment
from app.modules.finance.infrastructure.models.payout_item import PayoutItem


@dataclass(frozen=True)
class PayoutStatement:
    """O demonstrativo do artista (RN-REP-007).

    A regra lista o que ele exibe: "sessões incluídas, valor recebido por sessão,
    percentual aplicado, ajustes positivos ou negativos e total líquido". As três
    peças vêm juntas porque é assim que se lê — um repasse sem os itens é um
    número sem explicação, e é justamente a explicação que o artista confere
    contra o próprio extrato.

    Imutável: descreve um fechamento já ocorrido."""

    payout: Payout
    items: list[PayoutItem]
    adjustments: list[PayoutAdjustment]
