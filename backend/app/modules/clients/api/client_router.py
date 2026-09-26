import uuid

from fastapi import APIRouter, Request, status

from app.core.container import Container
from app.modules.clients.api.client_contact_response import ClientContactResponse
from app.modules.clients.api.client_request import ClientRequest
from app.modules.clients.api.client_response import ClientResponse
from app.modules.clients.api.merge_clients_request import MergeClientsRequest
from app.modules.clients.api.registered_client_response import RegisteredClientResponse
from app.modules.identity.api.session_authenticator import SessionAuthenticator
from app.shared.errors.business_rule_error import BusinessRuleError


class ClientRouter:
    """Cadastro de clientes (RN-CLI-001 a RN-CLI-006)."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._authenticator = SessionAuthenticator(container)

    def build(self) -> APIRouter:
        router = APIRouter(prefix="/clients", tags=["clients"])
        router.add_api_route(
            "", self.list_clients, methods=["GET"], response_model=list[ClientResponse]
        )
        router.add_api_route(
            "",
            self.register_client,
            methods=["POST"],
            response_model=RegisteredClientResponse,
            status_code=status.HTTP_201_CREATED,
        )
        router.add_api_route("/{client_id}", self.get_client, methods=["GET"])
        router.add_api_route(
            "/{client_id}", self.update_client, methods=["PUT"], response_model=ClientResponse
        )
        router.add_api_route(
            "/merge", self.merge_clients, methods=["POST"], response_model=ClientResponse
        )
        return router

    def list_clients(self, request: Request) -> list[ClientResponse]:
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            clients = self._container.clients.list_clients(session).execute(actor)
            return [ClientResponse.from_model(client) for client in clients]

    def register_client(
        self, payload: ClientRequest, request: Request
    ) -> RegisteredClientResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)

        with self._container.database.session() as session:
            client, duplicates = self._container.clients.register_client(session).execute(
                actor=actor,
                name=payload.name,
                phone=payload.phone,
                instagram=payload.instagram,
            )
            return RegisteredClientResponse(
                client=ClientResponse.from_model(client),
                possible_duplicates=[
                    ClientContactResponse.from_model(duplicate) for duplicate in duplicates
                ],
            )

    def get_client(
        self, client_id: uuid.UUID, request: Request
    ) -> ClientResponse | ClientContactResponse:
        """RN-CLI-004: a resposta muda de forma conforme quem pergunta.

        Quem não cadastrou o cliente recebe apenas o contato — não um 403. O
        artista indicado precisa dos dados para atender, mas não do histórico."""
        actor = self._authenticator.require_user(request)

        with self._container.database.session() as session:
            client = self._container.clients.clients(session).find_by_id(client_id)
            if client is None or client.merged_into_id is not None:
                raise BusinessRuleError("Client not found.")

            policy = self._container.clients.policy
            if policy.can_see_full_record(actor, client.registered_by_artist_id):
                return ClientResponse.from_model(client)
            return ClientContactResponse.from_model(client)

    def update_client(
        self, client_id: uuid.UUID, payload: ClientRequest, request: Request
    ) -> ClientResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)

        with self._container.database.session() as session:
            client = self._container.clients.update_client(session).execute(
                actor=actor,
                client_id=client_id,
                name=payload.name,
                phone=payload.phone,
                instagram=payload.instagram,
            )
            return ClientResponse.from_model(client)

    def merge_clients(self, payload: MergeClientsRequest, request: Request) -> ClientResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)

        with self._container.database.session() as session:
            survivor = self._container.clients.merge_clients(session).execute(
                actor=actor,
                duplicate_id=payload.duplicate_id,
                survivor_id=payload.survivor_id,
            )
            return ClientResponse.from_model(survivor)
