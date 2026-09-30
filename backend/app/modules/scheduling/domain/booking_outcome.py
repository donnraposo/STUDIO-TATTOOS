from enum import StrEnum


class BookingOutcome(StrEnum):
    """O desfecho do agendamento, na linguagem da agenda.

    Existe separado do `SettlementEvent` do financeiro de propósito: a agenda
    descreve o que aconteceu com o horário, o financeiro traduz isso em destino
    do dinheiro. Compartilhar um enum só faria a agenda importar o vocabulário
    do financeiro para poder chamá-lo — exatamente a dependência que a porta
    existe para evitar.

    `RESCHEDULED_IN_TIME` e `RESCHEDULED_LATE` são separados porque a RN-AGE-008
    os trata de forma oposta, e quem sabe se o aviso veio dentro das 24 horas é a
    agenda, que tem o horário original em mão."""

    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    RESCHEDULED_IN_TIME = "RESCHEDULED_IN_TIME"
    RESCHEDULED_LATE = "RESCHEDULED_LATE"
