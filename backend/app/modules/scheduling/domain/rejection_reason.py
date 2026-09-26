from enum import StrEnum


class RejectionReason(StrEnum):
    """Motivos previstos para recusar uma solicitação (RN-AGE-006).

    A lista é fechada de propósito: o motivo alimenta o tratamento financeiro do
    sinal e relatórios de cancelamento. Observação livre é campo à parte."""

    SLOT_TAKEN = "SLOT_TAKEN"
    STUDIO_CLOSED = "STUDIO_CLOSED"
    RESCHEDULED = "RESCHEDULED"
