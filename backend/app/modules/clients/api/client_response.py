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
    #: Nulo significa indicação do estúdio: a ausência é o dado (RN-CLI-002).
    brought_by_artist_id: uuid.UUID | None
    created_at: datetime

    @classmethod
    def from_model(cls, client: Client) -> "ClientResponse":
        return cls(
            id=client.id,
            name=client.name,
            phone=client.phone,
            instagram=client.instagram,
            registered_by_artist_id=client.registered_by_artist_id,
            brought_by_artist_id=client.brought_by_artist_id,
            created_at=client.created_at,
        )
