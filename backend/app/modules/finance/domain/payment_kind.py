from enum import StrEnum


class PaymentKind(StrEnum):
    """O que o pagamento cobre (RN-PAG-001, RN-PAG-004 e RN-GST-001).

    `DEPOSIT` é o sinal de €50 que confirma um agendamento. Ele não é um valor
    adicional: integra o preço da tatuagem e a base do repasse quando o
    atendimento acontece (RN-PAG-005).

    `BALANCE` é o restante da sessão, pago até a conclusão dela (RN-PAG-008).

    `FULL_PREPAY` é o preço integral antecipado, registrado pelo gestor durante
    a aprovação (RN-PAG-004).

    `GUEST_WEEK` é a taxa semanal do guest. Existe aqui porque o modelo de dados
    já o previa; a semana do guest é de outra sprint."""

    DEPOSIT = "DEPOSIT"
    BALANCE = "BALANCE"
    FULL_PREPAY = "FULL_PREPAY"
    GUEST_WEEK = "GUEST_WEEK"
