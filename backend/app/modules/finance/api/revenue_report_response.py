from pydantic import BaseModel

from app.modules.finance.api.revenue_line_response import RevenueLineResponse
from app.modules.finance.api.revenue_totals_response import RevenueTotalsResponse
from app.modules.finance.domain.revenue_report import RevenueReport


class RevenueReportResponse(BaseModel):
    """O faturamento de um mes: detalhamento e rodape juntos (RN 10.4).

    Juntos porque e assim que a planilha se le -- os totais sozinhos sao um
    numero sem explicacao, e e a explicacao que se confere linha a linha quando
    a conta nao bate."""

    year: int
    month: int
    lines: list[RevenueLineResponse]
    totals: RevenueTotalsResponse

    @classmethod
    def from_report(cls, report: RevenueReport) -> "RevenueReportResponse":
        return cls(
            year=report.year,
            month=report.month,
            lines=[RevenueLineResponse.from_line(line) for line in report.lines],
            totals=RevenueTotalsResponse.from_totals(report.totals),
        )
