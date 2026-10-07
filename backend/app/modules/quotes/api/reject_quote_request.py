from pydantic import BaseModel, Field


class RejectQuoteRequest(BaseModel):
    """Recusa de orçamento (RN-ORC-003).

    Motivo é obrigatório e de texto livre, ao contrário da recusa de agendamento,
    que tem lista fechada. `min_length` impede que um campo vazio satisfaça a
    exigência de motivo."""

    reason: str = Field(min_length=3, max_length=500)
    note: str | None = Field(default=None, max_length=1000)
