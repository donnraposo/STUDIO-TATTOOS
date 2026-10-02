import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.models.payout_item import PayoutItem


class PayoutItemRepository:
    """Acesso aos itens de um repasse."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, item: PayoutItem) -> PayoutItem:
        self._session.add(item)
        self._session.flush()
        return item

    def list_for_payout(self, payout_id: uuid.UUID) -> list[PayoutItem]:
        statement = (
            select(PayoutItem)
            .where(PayoutItem.payout_id == payout_id)
            .order_by(PayoutItem.created_at)
        )
        return list(self._session.execute(statement).scalars())

    def paid_session_ids(self) -> set[uuid.UUID]:
        """As sessoes que ja entraram em algum repasse.

        E o filtro que impede pagar duas vezes pelo mesmo trabalho. O indice
        unico recusaria a segunda gravacao de qualquer forma, mas quem calcula
        precisa saber antes -- senao o fechamento inteiro falharia por causa de
        uma sessao que nao deveria estar na lista."""
        return set(self._session.execute(select(PayoutItem.session_id)).scalars())
