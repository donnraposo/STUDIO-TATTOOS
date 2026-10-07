from dataclasses import dataclass

from app.modules.finance.domain.revenue_line import RevenueLine
from app.modules.finance.domain.revenue_totals import RevenueTotals


@dataclass(frozen=True)
class RevenueReport:
    """O faturamento de um mês: o detalhamento e o rodapé (RN 10.4).

    Os dois juntos porque é assim que a planilha do estúdio se lê — os totais
    sozinhos são um número sem explicação, e é a explicação que se confere
    linha a linha quando a conta não bate.

    Imutável."""

    year: int
    month: int
    lines: list[RevenueLine]
    totals: RevenueTotals
