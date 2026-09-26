from pydantic import BaseModel

from app.modules.clients.api.client_contact_response import ClientContactResponse
from app.modules.clients.api.client_response import ClientResponse


class RegisteredClientResponse(BaseModel):
    """Resposta do cadastro, com o alerta de duplicidade junto.

    O aviso vem no mesmo retorno de propósito: a RN-CLI-005 manda alertar sem
    bloquear, então o cadastro já está feito e cabe a quem cadastrou decidir se
    era mesmo a mesma pessoa."""

    client: ClientResponse
    possible_duplicates: list[ClientContactResponse]
