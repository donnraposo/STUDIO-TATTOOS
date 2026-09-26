import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.quotes.infrastructure.models.quote import Quote


class QuoteRepository:
    """Acesso aos orçamentos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, quote: Quote) -> Quote:
        self._session.add(quote)
        self._session.flush()
        return quote

    def find_by_id(self, quote_id: uuid.UUID) -> Quote | None:
        return self._session.get(Quote, quote_id)

    def list_all(self) -> list[Quote]:
        statement = select(Quote).order_by(Quote.created_at.desc())
        return list(self._session.execute(statement).scalars())

    def list_for_artist(self, artist_id: uuid.UUID) -> list[Quote]:
        statement = (
            select(Quote)
            .where(Quote.artist_id == artist_id)
            .order_by(Quote.created_at.desc())
        )
        return list(self._session.execute(statement).scalars())
