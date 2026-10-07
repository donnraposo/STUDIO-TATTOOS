import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.infrastructure.models.quote import Quote


class QuoteRepository:
    """Acesso aos orçamentos.

    O filtro por estado serve ao painel do gestor (seção 10.1): os pendentes,
    que não têm vencimento automático (RN-ORC-002) e por isso ficam esperando
    decisão pelo tempo que for, sem nada cobrar atenção."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, quote: Quote) -> Quote:
        self._session.add(quote)
        self._session.flush()
        return quote

    def find_by_id(self, quote_id: uuid.UUID) -> Quote | None:
        return self._session.get(Quote, quote_id)

    def list_all(self, status: QuoteStatus | None = None) -> list[Quote]:
        return self._fetch(select(Quote), status)

    def list_for_artist(
        self, artist_id: uuid.UUID, status: QuoteStatus | None = None
    ) -> list[Quote]:
        return self._fetch(select(Quote).where(Quote.artist_id == artist_id), status)

    def _fetch(self, statement: Select[tuple[Quote]], status: QuoteStatus | None) -> list[Quote]:
        if status is not None:
            statement = statement.where(Quote.status == status)
        ordered = statement.order_by(Quote.created_at.desc())
        return list(self._session.execute(ordered).scalars())
