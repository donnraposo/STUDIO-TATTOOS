from enum import StrEnum


class SessionStatus(StrEnum):
    """Estados da sessão (RN-ORC-005 e RN-ORC-006).

    `DONE` e `PAID_OFF` são separados de propósito: o artista marca a sessão
    como realizada, mas ela só entra em repasse depois de o gestor confirmar o
    recebimento integral. Um único estado para as duas coisas colocaria no
    repasse trabalho ainda não pago.

    `PARTIALLY_DONE` existe porque sessão interrompida gera repasse apenas
    sobre o valor efetivamente recebido, não sobre o previsto."""

    SCHEDULED = "SCHEDULED"
    DONE = "DONE"
    PARTIALLY_DONE = "PARTIALLY_DONE"
    PAID_OFF = "PAID_OFF"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
