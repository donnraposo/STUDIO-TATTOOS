import uuid

from app.modules.quotes.api.quote_fields_request import QuoteFieldsRequest


class QuoteRequest(QuoteFieldsRequest):
    """Orçamento novo: os campos editáveis mais a identidade do atendimento.

    `artist_id` só é aceito de gestor orçando para outra pessoa; o residente
    orçando para si pode omitir. É por aqui que o gestor cria o orçamento de uma
    indicação do estúdio atendida por guest, que não acessa o módulo
    (RN-ORC-001).

    A edição usa a classe base, sem estes dois campos: reatribuir um orçamento a
    outro cliente ou artista não é edição. Se o atendimento é de outra pessoa, é
    outro orçamento."""

    client_id: uuid.UUID
    artist_id: uuid.UUID | None = None
