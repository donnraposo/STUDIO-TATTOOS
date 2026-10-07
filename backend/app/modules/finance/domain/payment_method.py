from enum import StrEnum


class PaymentMethod(StrEnum):
    """Como o dinheiro entrou ou saiu (RN-PAG-002 e RN-PAG-006).

    Nesta versão os três são lançados à mão pelo gestor. Não há integração com
    operadora, terminal ou gateway: quando o cartão passa numa solução externa,
    os dados da transação são digitados aqui (RN-PAG-006).

    A devolução pode usar forma diferente da original (RN-PAG-009), e é por isso
    que o mesmo conjunto serve aos dois lados."""

    BANK_TRANSFER = "BANK_TRANSFER"
    CASH = "CASH"
    CARD = "CARD"
