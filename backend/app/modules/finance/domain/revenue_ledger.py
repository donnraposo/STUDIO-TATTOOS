import uuid
from decimal import Decimal

from app.modules.finance.domain.payout_share import PayoutShare
from app.modules.finance.domain.revenue_line import RevenueLine
from app.modules.finance.domain.revenue_totals import RevenueTotals
from app.modules.finance.domain.settled_session import SettledSession


class RevenueLedger:
    """Transforma atendimentos quitados nas linhas e nos totais do período
    (RN 10.4 e RN-REP-007).

    **Usa o mesmo `PayoutShare` do repasse, e é o ponto inteiro.** Se o
    relatório calculasse a divisão por conta própria, o estúdio teria dois
    números para a mesma coisa: o que o painel mostra e o que o artista recebe.
    Divergindo em um centavo por arredondamento, a conversa que se segue não é
    sobre software.

    **A parte do estúdio é o resto, não uma segunda multiplicação.** Calcular os
    dois lados separadamente faria a soma falhar por um centavo sempre que o
    arredondamento subisse — e a planilha do estúdio é conferida justamente por
    `total = artistas + casa`.

    **O sinal não abate** (RN-PAG-005): "o sinal integrará o preço da tatuagem e
    a base de cálculo do repasse". Ele já está dentro do valor cobrado, e
    subtraí-lo aqui pagaria o artista a menos.

    Classe pura: não conhece banco, ator nem transação."""

    def __init__(self, share: PayoutShare) -> None:
        self._share = share

    def lines(
        self, sessions: list[SettledSession], transferred: set[uuid.UUID]
    ) -> list[RevenueLine]:
        return [
            RevenueLine(
                session_id=session.session_id,
                artist_id=session.artist_id,
                settled_at=session.confirmed_at,
                value=session.received_amount,
                percentage=session.percentage,
                artist_amount=self._share.of(session.received_amount, session.percentage),
                studio_amount=session.received_amount
                - self._share.of(session.received_amount, session.percentage),
                transferred=session.session_id in transferred,
            )
            for session in sessions
        ]

    def totals(self, lines: list[RevenueLine]) -> RevenueTotals:
        return RevenueTotals(
            sessions=len(lines),
            value=sum((line.value for line in lines), Decimal("0.00")),
            artists=sum((line.artist_amount for line in lines), Decimal("0.00")),
            studio=sum((line.studio_amount for line in lines), Decimal("0.00")),
        )
