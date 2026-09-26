import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.clients.infrastructure.models.client import Client


class ClientRepository:
    """Acesso ao cadastro de clientes.

    As consultas ignoram registros já unidos a outro cadastro
    (`merged_into_id`), para que uma duplicidade resolvida não volte a aparecer
    nas listas."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, client: Client) -> Client:
        self._session.add(client)
        self._session.flush()
        return client

    def find_by_id(self, client_id: uuid.UUID) -> Client | None:
        return self._session.get(Client, client_id)

    def list_all(self) -> list[Client]:
        statement = (
            select(Client).where(Client.merged_into_id.is_(None)).order_by(Client.name)
        )
        return list(self._session.execute(statement).scalars())

    def list_registered_by(self, artist_id: uuid.UUID) -> list[Client]:
        statement = (
            select(Client)
            .where(
                Client.registered_by_artist_id == artist_id,
                Client.merged_into_id.is_(None),
            )
            .order_by(Client.name)
        )
        return list(self._session.execute(statement).scalars())

    def find_possible_duplicates(
        self, phone: str, instagram: str | None, excluding: uuid.UUID | None = None
    ) -> list[Client]:
        """RN-CLI-005: alerta por telefone e, quando informado, Instagram.

        Devolve candidatos para que a aplicação avise; nunca bloqueia."""
        criteria = [Client.phone == phone.strip()]
        if instagram:
            criteria.append(Client.instagram == instagram.strip())

        statement = select(Client).where(
            or_(*criteria), Client.merged_into_id.is_(None)
        )
        if excluding is not None:
            statement = statement.where(Client.id != excluding)
        return list(self._session.execute(statement).scalars())

    def has_any_registered_by(self, artist_id: uuid.UUID, client_id: uuid.UUID) -> bool:
        client = self.find_by_id(client_id)
        return client is not None and client.registered_by_artist_id == artist_id
