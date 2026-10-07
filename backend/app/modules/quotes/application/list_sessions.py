import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.session_policy import SessionPolicy
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.quotes.infrastructure.tattoo_session_repository import TattooSessionRepository
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ListSessions:
    """As sessões de um orçamento, para quem pode ver o orçamento.

    A permissão é conferida contra o artista do orçamento, e não contra a
    sessão: sessão não tem dono próprio — ela pertence ao trabalho, e quem pode
    ver o trabalho pode ver o plano dele."""

    def __init__(
        self,
        sessions: TattooSessionRepository,
        quotes: QuoteRepository,
        policy: SessionPolicy,
    ) -> None:
        self._sessions = sessions
        self._quotes = quotes
        self._policy = policy

    def execute(self, actor: AuthenticatedUser, quote_id: uuid.UUID) -> list[TattooSession]:
        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if not self._policy.can_see(actor, quote.artist_id):
            raise PermissionDeniedError("You cannot see the sessions of this quote.")

        return self._sessions.list_for_quote(quote_id)
