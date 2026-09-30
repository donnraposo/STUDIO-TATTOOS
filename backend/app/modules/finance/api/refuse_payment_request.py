from pydantic import BaseModel, Field


class RefusePaymentRequest(BaseModel):
    """Recusa de um recebimento informado (RN-PAG-007).

    Motivo obrigatorio: o lancamento permanece no historico, e um registro
    recusado sem explicacao nao diz a ninguem por que o comprovante nao valeu."""

    reason: str = Field(min_length=3, max_length=500)
