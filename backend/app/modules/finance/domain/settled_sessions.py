from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.finance.domain.settled_session import SettledSession


class SettledSessions(ABC):
    """Porta pela qual o financeiro pergunta o que foi quitado numa semana.

    Quem sabe responder é o módulo de orçamentos, dono das sessões. Quem
    **precisa** da resposta é o repasse — e por isso a porta é dele, como no
    acerto entre agenda e financeiro (ADR-028).

    Se o financeiro consultasse a tabela de sessões direto, o cálculo do repasse
    passaria a depender do desenho interno daquele módulo, e mexer lá quebraria
    o pagamento dos artistas. Com a porta aqui, o orçamento implementa e a raiz
    de composição liga os dois.

    O intervalo é **aberto no começo e fechado no fim**: o que foi confirmado
    exatamente às 20h de sexta pertence à semana que fecha (RN-REP-004)."""

    @abstractmethod
    def settled_between(self, opening: datetime, closing: datetime) -> list[SettledSession]:
        """As sessões quitadas na janela, de todos os artistas."""
