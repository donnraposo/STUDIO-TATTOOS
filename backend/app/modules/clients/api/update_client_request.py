import uuid

from app.modules.clients.api.client_contact_request import ClientContactRequest
from app.modules.clients.domain.client_source import ClientSource


class UpdateClientRequest(ClientContactRequest):
    """Correção de um cliente existente (RN-CLI-006).

    **`source` é opcional aqui, e o padrão é não mexer.** Na criação ele tem
    padrão porque todo cliente vem de algum lugar; na edição, um padrão faria
    toda correção de telefone tentar reescrever a origem — e, como alterá-la é de
    gerente e proprietário (RN-CLI-003), o artista corrigindo um Instagram
    receberia 403 sem entender por quê.

    É por isso que criar e editar têm contratos separados em vez de um só com
    campos opcionais: o mesmo `None` significaria "use o padrão" num caso e "não
    toque" no outro."""

    source: ClientSource | None = None
    brought_by_artist_id: uuid.UUID | None = None
