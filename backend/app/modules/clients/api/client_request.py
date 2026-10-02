import uuid

from app.modules.clients.api.client_contact_request import ClientContactRequest
from app.modules.clients.domain.client_source import ClientSource


class ClientRequest(ClientContactRequest):
    """Cliente novo: o contato mais de onde ele veio (RN-CLI-002).

    `source` tem padrão porque o caso corrente é o artista cadastrando o próprio
    cliente. `STUDIO` significa indicação do estúdio e não admite artista;
    `ARTIST` sem `brought_by_artist_id` significa o próprio autor do cadastro.

    A contradição — `STUDIO` com artista junto — é recusada pelo caso de uso e
    não aqui, porque a regra também depende de quem pede: nomear outro artista é
    do gestor.

    **Isto não decide a origem do atendimento.** A RN-CLI-002 é explícita: "a
    origem será determinada em cada atendimento". O campo alimenta a sugestão do
    orçamento; quem decide é quem orça, e corrigir é do gestor (RN-CLI-003)."""

    source: ClientSource = ClientSource.ARTIST
    brought_by_artist_id: uuid.UUID | None = None
