from enum import StrEnum


class SettlementEvent(StrEnum):
    """O que aconteceu com o agendamento, do ponto de vista do dinheiro.

    São os quatro desfechos que as regras tratam de forma diferente:
    RN-PAG-003 (o estúdio recusou), RN-AGE-009 (cancelado sem nova data),
    RN-AGE-010 (não compareceu) e RN-AGE-008 (remarcado, dentro ou fora do prazo
    de 24 horas).

    `RESCHEDULED_IN_TIME` e `RESCHEDULED_LATE` são eventos distintos porque a
    regra os trata de forma oposta — dentro do prazo o sinal acompanha o novo
    horário, fora dele o cliente o perde. Um único evento com um booleano ao
    lado espalharia essa decisão por quem chama."""

    REJECTED_BY_STUDIO = "REJECTED_BY_STUDIO"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    RESCHEDULED_IN_TIME = "RESCHEDULED_IN_TIME"
    RESCHEDULED_LATE = "RESCHEDULED_LATE"
