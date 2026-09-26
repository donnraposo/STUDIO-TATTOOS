import uuid

from pydantic import BaseModel

from app.modules.clients.infrastructure.models.client import Client


class ClientContactResponse(BaseModel):
    """Projeção reduzida da RN-CLI-004.

    É o que o artista vê quando o estúdio lhe indica um cliente cadastrado por
    outro artista: apenas o necessário para atender. Sem data de cadastro, sem
    quem cadastrou e sem histórico anterior.

    A restrição está no formato da resposta, não em um filtro na rota — assim
    não há como esquecer de omitir um campo."""

    id: uuid.UUID
    name: str
    phone: str
    instagram: str | None

    @classmethod
    def from_model(cls, client: Client) -> "ClientContactResponse":
        return cls(
            id=client.id,
            name=client.name,
            phone=client.phone,
            instagram=client.instagram,
        )
