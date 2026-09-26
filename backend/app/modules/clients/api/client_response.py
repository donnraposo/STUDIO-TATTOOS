import uuid
from datetime import datetime

from pydantic import BaseModel

from app.modules.clients.infrastructure.models.client import Client


class ClientResponse(BaseModel):
    """Ficha completa. Só chega a proprietário, gerente e ao artista que
    cadastrou o cliente (RN-CLI-004)."""

    id: uuid.UUID
    name: str
    phone: str
    instagram: str | None
    registered_by_artist_id: uuid.UUID
    created_at: datetime

    @classmethod
    def from_model(cls, client: Client) -> "ClientResponse":
        return cls(
            id=client.id,
            name=client.name,
            phone=client.phone,
            instagram=client.instagram,
            registered_by_artist_id=client.registered_by_artist_id,
            created_at=client.created_at,
        )
