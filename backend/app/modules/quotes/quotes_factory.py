from sqlalchemy.orm import Session

from app.modules.quotes.application.approve_quote import ApproveQuote
from app.modules.quotes.application.create_quote import CreateQuote
from app.modules.quotes.application.get_quote import GetQuote
from app.modules.quotes.application.list_quotes import ListQuotes
from app.modules.quotes.application.reject_quote import RejectQuote
from app.modules.quotes.application.update_quote import UpdateQuote
from app.modules.quotes.domain.artist_percentage_policy import ArtistPercentagePolicy
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder


class QuotesFactory:
    """Monta os casos de uso dos orçamentos."""

    def __init__(self) -> None:
        self._policy = QuotePolicy()
        self._percentages = ArtistPercentagePolicy()

    @property
    def policy(self) -> QuotePolicy:
        return self._policy

    @property
    def percentages(self) -> ArtistPercentagePolicy:
        return self._percentages

    def quotes(self, session: Session) -> QuoteRepository:
        return QuoteRepository(session)

    def create_quote(self, session: Session) -> CreateQuote:
        return CreateQuote(
            quotes=self.quotes(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def update_quote(self, session: Session) -> UpdateQuote:
        return UpdateQuote(
            quotes=self.quotes(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def approve_quote(self, session: Session) -> ApproveQuote:
        return ApproveQuote(
            quotes=self.quotes(session),
            policy=self._policy,
            percentages=self._percentages,
            audit=AuditRecorder(session),
        )

    def reject_quote(self, session: Session) -> RejectQuote:
        return RejectQuote(
            quotes=self.quotes(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def list_quotes(self, session: Session) -> ListQuotes:
        return ListQuotes(quotes=self.quotes(session), policy=self._policy)

    def get_quote(self, session: Session) -> GetQuote:
        return GetQuote(quotes=self.quotes(session), policy=self._policy)
