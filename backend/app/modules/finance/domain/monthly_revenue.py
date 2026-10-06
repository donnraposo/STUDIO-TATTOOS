from dataclasses import dataclass

from app.modules.finance.domain.revenue_totals import RevenueTotals


@dataclass(frozen=True)
class MonthlyRevenue:
    """Um mês na comparação entre meses (RN 10.4).

    Só os totais, sem as linhas: a comparação responde "como foi este mês contra
    o anterior", e carregar o detalhamento de doze meses para desenhar doze
    barras traria o ano inteiro de atendimentos ao navegador. Quem quer o
    detalhe abre o mês.

    Imutável."""

    year: int
    month: int
    totals: RevenueTotals
