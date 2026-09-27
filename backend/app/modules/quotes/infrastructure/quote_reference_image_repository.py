import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.quotes.infrastructure.models.quote_reference_image import QuoteReferenceImage


class QuoteReferenceImageRepository:
    """Acesso às imagens de referência de um orçamento."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, image: QuoteReferenceImage) -> QuoteReferenceImage:
        self._session.add(image)
        self._session.flush()
        return image

    def find_by_id(self, image_id: uuid.UUID) -> QuoteReferenceImage | None:
        return self._session.get(QuoteReferenceImage, image_id)

    def list_for_quote(self, quote_id: uuid.UUID) -> list[QuoteReferenceImage]:
        statement = (
            select(QuoteReferenceImage)
            .where(QuoteReferenceImage.quote_id == quote_id)
            .order_by(QuoteReferenceImage.uploaded_at)
        )
        return list(self._session.execute(statement).scalars())

    def count_for_quote(self, quote_id: uuid.UUID) -> int:
        """Conta no banco em vez de carregar a lista para medir o tamanho: o
        limite por orçamento não precisa das linhas, só do número."""
        statement = (
            select(func.count())
            .select_from(QuoteReferenceImage)
            .where(QuoteReferenceImage.quote_id == quote_id)
        )
        return self._session.execute(statement).scalar_one()

    def remove(self, image: QuoteReferenceImage) -> None:
        self._session.delete(image)
        self._session.flush()
