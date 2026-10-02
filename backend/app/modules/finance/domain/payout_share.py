from decimal import ROUND_HALF_UP, Decimal


class PayoutShare:
    """O quanto cabe ao artista sobre um valor recebido (RN-REP-007).

    **Por sessão, e arredondado a duas casas em cada uma.** A regra é literal: "o
    repasse será calculado separadamente para cada sessão e arredondado para duas
    casas decimais; o fechamento semanal somará os valores calculados por
    sessão". Somar primeiro e arredondar no fim dá outro número, e a diferença
    aparece no bolso do artista.

    `ROUND_HALF_UP` e não o padrão do Python, que é `ROUND_HALF_EVEN`. Meio
    centavo arredonda para cima, como se faz com dinheiro em nota fiscal: o
    arredondamento bancário é estatisticamente mais justo e contabilmente
    surpreendente, e ninguém quer explicar ao artista por que €0,125 virou €0,12
    numa semana e €0,13 na outra.

    Classe pura: não conhece sessão, banco nem ator. Recebe dois números e
    devolve um."""

    _CENTS = Decimal("0.01")
    _HUNDRED = Decimal("100")

    def of(self, received: Decimal, percentage: Decimal) -> Decimal:
        return (received * percentage / PayoutShare._HUNDRED).quantize(
            PayoutShare._CENTS, rounding=ROUND_HALF_UP
        )
