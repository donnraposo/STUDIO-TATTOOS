from app.modules.finance.domain.monthly_revenue import MonthlyRevenue
from app.modules.finance.domain.revenue_ledger import RevenueLedger
from app.modules.finance.domain.revenue_month import RevenueMonth
from app.modules.finance.domain.revenue_policy import RevenuePolicy
from app.modules.finance.domain.settled_sessions import SettledSessions
from app.modules.finance.infrastructure.payout_item_repository import PayoutItemRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.shared.errors.permission_denied_error import PermissionDeniedError


class CompareRevenueMonths:
    """Os totais mês a mês, para o estúdio ver como anda (RN 10.4).

    **Só os totais.** A pergunta é "como foi este mês contra o anterior", e
    carregar o detalhamento de doze meses para desenhar doze barras traria o ano
    inteiro de atendimentos ao navegador. Quem quer o detalhe abre o mês.

    **Mês sem atendimento aparece zerado, e não some.** Um buraco na sequência
    faria o gráfico mentir sobre o tempo: dezembro vazio ao lado de novembro
    cheio é informação, e dezembro ausente parece que novembro foi ontem.

    Doze meses é o recorte que responde "e no ano?" sem virar consulta de
    histórico. Quem quiser mais pede mais."""

    def __init__(
        self,
        sessions: SettledSessions,
        items: PayoutItemRepository,
        ledger: RevenueLedger,
        months: RevenueMonth,
        policy: RevenuePolicy,
    ) -> None:
        self._sessions = sessions
        self._items = items
        self._ledger = ledger
        self._months = months
        self._policy = policy

    def execute(
        self, actor: AuthenticatedUser, year: int, month: int, count: int = 12
    ) -> list[MonthlyRevenue]:
        if not self._policy.can_see(actor):
            raise PermissionDeniedError("You cannot see the studio revenue.")

        transferred = self._items.transferred_session_ids()
        compared: list[MonthlyRevenue] = []

        for each_year, each_month in self._months.recent(year, month, count):
            start, end = self._months.bounds_for(each_year, each_month)
            lines = self._ledger.lines(self._sessions.settled_between(start, end), transferred)
            compared.append(
                MonthlyRevenue(
                    year=each_year, month=each_month, totals=self._ledger.totals(lines)
                )
            )

        return compared
