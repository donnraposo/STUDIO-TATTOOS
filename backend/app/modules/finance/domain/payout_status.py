from enum import StrEnum


class PayoutStatus(StrEnum):
    """Estados do repasse (RN-REP-007).

    `CALCULATED` é o fechamento feito e ainda não transferido; `PAID` é a
    transferência confirmada pelo gestor; `ADJUSTED` é o repasse que recebeu
    lançamento negativo depois de pago (RN-REP-005).

    **`ADJUSTED` não substitui `PAID`.** Ele marca o repasse **seguinte**, que
    carrega o desconto — o fechamento anterior permanece pago e intocado, porque
    a regra é explícita: "uma devolução ocorrida depois do pagamento do repasse
    não alterará o fechamento anterior"."""

    CALCULATED = "CALCULATED"
    PAID = "PAID"
    ADJUSTED = "ADJUSTED"
