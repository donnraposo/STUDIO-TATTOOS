from app.modules.finance.domain.revenue_ledger import RevenueLedger
from app.modules.finance.domain.revenue_month import RevenueMonth
from app.modules.finance.domain.revenue_policy import RevenuePolicy
from app.modules.finance.domain.revenue_report import RevenueReport
from app.modules.finance.domain.settled_sessions import SettledSessions
from app.modules.finance.infrastructure.payout_item_repository import PayoutItemRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.shared.errors.permission_denied_error import PermissionDeniedError


class GetRevenueReport:
    """O faturamento de um mês, linha a linha (RN 10.4).

    É o controle que o estúdio mantinha em planilha: cada atendimento quitado
    com o valor, o percentual congelado, a comissão do tatuador e a parte da
    casa, mais os três totais do rodapé.

    **Lê o que já está gravado e não grava nada.** Um relatório que corrigisse
    dado ao passar seria um relatório que muda o passado — e a RN-PAG-007 já diz
    que correção entra como lançamento vinculado, não como edição.

    **Só entra sessão quitada** (RN-PAG-008), pela mesma porta que o repasse usa.
    Sessão realizada e ainda não confirmada pelo gestor está fora: contá-la
    mostraria um faturamento que o estúdio ainda não viu entrar, e o número do
    painel deixaria de bater com o do banco."""

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

    def execute(self, actor: AuthenticatedUser, year: int, month: int) -> RevenueReport:
        if not self._policy.can_see(actor):
            raise PermissionDeniedError("You cannot see the studio revenue.")

        start, end = self._months.bounds_for(year, month)
        settled = self._sessions.settled_between(start, end)
        lines = self._ledger.lines(settled, self._items.transferred_session_ids())

        return RevenueReport(
            year=year, month=month, lines=lines, totals=self._ledger.totals(lines)
        )
