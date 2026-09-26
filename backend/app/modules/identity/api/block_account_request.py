from pydantic import BaseModel, Field


class BlockAccountRequest(BaseModel):
    """Bloqueio exige motivo: a decisao precisa ficar rastreavel no historico
    e na auditoria (RN 2.5)."""

    reason: str = Field(min_length=1, max_length=200)
