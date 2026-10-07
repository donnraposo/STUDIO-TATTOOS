from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RevenueTotals:
    """Os três números do rodapé da planilha do estúdio.

    `value` é o total tatuado, `artists` o que foi para os tatuadores e `studio`
    o que ficou com a casa — e os dois últimos somam o primeiro.

    **São somas de linhas já arredondadas**, e não o arredondamento de uma soma.
    A RN-REP-007 manda calcular por sessão e arredondar em cada uma; somar
    primeiro daria um total que não confere com nenhuma das linhas que o
    explicam, e seria o total que o estúdio conferiria contra o extrato.

    Imutável."""

    sessions: int
    value: Decimal
    artists: Decimal
    studio: Decimal
