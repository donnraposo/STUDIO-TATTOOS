from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository


class ListQuotes:
    """Lista os orçamentos visíveis ao ator.

    O gestor vê todos; o artista vê os seus. O recorte é feito na consulta, e
    não filtrando depois de trazer tudo: o que não deve ser visto não sai do
    banco. O mesmo vale para o estado: o painel do gestor pede os pendentes, e
    trazer todos para o navegador escolher desperdiçaria a consulta."""

    def __init__(self, quotes: QuoteRepository, policy: QuotePolicy) -> None:
        self._quotes = quotes
        self._policy = policy

    def execute(
        self, actor: AuthenticatedUser, status: QuoteStatus | None = None
    ) -> list[Quote]:
        if self._policy.sees_every_quote(actor):
            return self._quotes.list_all(status)
        return self._quotes.list_for_artist(actor.id, status)
