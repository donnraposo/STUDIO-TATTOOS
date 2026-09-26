import uuid

from pydantic import BaseModel


class MergeClientsRequest(BaseModel):
    """União de duplicidade. `duplicate_id` passa a apontar para `survivor_id`;
    nenhum registro é apagado (RN-CLI-006)."""

    duplicate_id: uuid.UUID
    survivor_id: uuid.UUID
