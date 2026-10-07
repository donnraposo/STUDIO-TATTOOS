import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class GetQuote:
    """Devolve um orçamento, se o ator puder vê-lo."""

    def __init__(self, quotes: QuoteRepository, policy: QuotePolicy) -> None:
        self._quotes = quotes
        self._policy = policy

    def execute(self, actor: AuthenticatedUser, quote_id: uuid.UUID) -> Quote:
        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if not self._policy.can_see(actor, quote.artist_id):
            raise PermissionDeniedError("You cannot see this quote.")

        return quote
