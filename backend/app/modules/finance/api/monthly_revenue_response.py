from pydantic import BaseModel

from app.modules.finance.api.revenue_totals_response import RevenueTotalsResponse
from app.modules.finance.domain.monthly_revenue import MonthlyRevenue


class MonthlyRevenueResponse(BaseModel):
    """Um mes na comparacao. So os totais: quem quer o detalhe abre o mes."""

    year: int
    month: int
    totals: RevenueTotalsResponse

    @classmethod
    def from_month(cls, month: MonthlyRevenue) -> "MonthlyRevenueResponse":
        return cls(
            year=month.year,
            month=month.month,
            totals=RevenueTotalsResponse.from_totals(month.totals),
        )
