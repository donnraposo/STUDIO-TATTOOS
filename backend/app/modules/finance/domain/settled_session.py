import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class SettledSession:
    """Uma sessão realizada e quitada, na forma que o repasse precisa
    (RN-PAG-008 e RN-REP-003).

    É o mínimo para calcular: de quem é, quanto entrou, qual o percentual
    congelado e quando o estúdio reconheceu o dinheiro. Nada do orçamento, nada
    do cliente — se o repasse carregasse a sessão inteira, passaria a depender do
    formato de outro módulo, e qualquer mudança lá mexeria nele.

    **`percentage` vem congelado da sessão** (RN-REP-006), não do padrão vigente.
    Mudar o percentual do estúdio hoje não pode alcançar trabalho aprovado meses
    atrás, e é por isso que ele viaja junto em vez de ser consultado.

    **`confirmed_at` é o que decide a semana**, e não a data em que a tatuagem
    foi feita. A RN-REP-004 fala em "pagamentos recebidos": o que conta é quando
    o estúdio reconheceu o dinheiro.

    Imutável: descreve um fato já ocorrido."""

    session_id: uuid.UUID
    artist_id: uuid.UUID
    received_amount: Decimal
    percentage: Decimal
    confirmed_at: datetime
