from enum import StrEnum


class BookingStatus(StrEnum):
    """Estados do agendamento (RN-AGE-003).

    `Solicitada → Aprovada ou Rejeitada → Realizada, Cancelada ou Não compareceu`

    A separação entre REQUESTED e APPROVED é o que sustenta a RN-AGE-004: uma
    solicitação pendente não bloqueia a maca para outros artistas, mas já ocupa
    a agenda do próprio artista."""

    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
