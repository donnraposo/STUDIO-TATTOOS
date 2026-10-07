from fastapi import APIRouter, Query, Request

from app.core.container import Container
from app.modules.finance.api.monthly_revenue_response import MonthlyRevenueResponse
from app.modules.finance.api.revenue_report_response import RevenueReportResponse
from app.modules.identity.api.session_authenticator import SessionAuthenticator


class RevenueRouter:
    """Faturamento do estudio (RN 10.4).

    **Somente leitura, e sem rota de escrita nenhuma.** Um relatorio que
    corrigisse dado ao passar seria um relatorio que muda o passado; correcao
    entra como lancamento vinculado, onde o fato aconteceu (RN-PAG-007).

    Mes e ano vao na consulta e nao no caminho porque sao recorte, nao
    identidade: `/revenue/2026/10` sugeriria um recurso chamado outubro."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._authenticator = SessionAuthenticator(container)

    def build(self) -> APIRouter:
        router = APIRouter(prefix="/revenue", tags=["revenue"])
        router.add_api_route(
            "", self.month, methods=["GET"], response_model=RevenueReportResponse
        )
        router.add_api_route(
            "/monthly",
            self.monthly,
            methods=["GET"],
            response_model=list[MonthlyRevenueResponse],
        )
        return router

    def month(
        self,
        request: Request,
        year: int = Query(ge=2000, le=2100),
        month: int = Query(ge=1, le=12),
    ) -> RevenueReportResponse:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            report = self._container.finance.revenue_report(session).execute(
                actor, year, month
            )
            return RevenueReportResponse.from_report(report)

    def monthly(
        self,
        request: Request,
        year: int = Query(ge=2000, le=2100),
        month: int = Query(ge=1, le=12),
        count: int = Query(default=12, ge=1, le=36),
    ) -> list[MonthlyRevenueResponse]:
        """Os `count` meses que terminam no mes pedido, do mais antigo ao mais
        novo. O teto de 36 existe para que a comparacao continue sendo
        comparacao: pedir duzentos meses seria consulta de historico, e o
        relatorio nao e isso."""
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            months = self._container.finance.compare_revenue(session).execute(
                actor, year, month, count
            )
            return [MonthlyRevenueResponse.from_month(each) for each in months]
