import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.models.payout_adjustment import PayoutAdjustment


class PayoutAdjustmentRepository:
    """Acesso aos ajustes negativos (RN-REP-005)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, adjustment: PayoutAdjustment) -> PayoutAdjustment:
        self._session.add(adjustment)
        self._session.flush()
        return adjustment

    def list_for_payout(self, payout_id: uuid.UUID) -> list[PayoutAdjustment]:
        statement = (
            select(PayoutAdjustment)
            .where(PayoutAdjustment.payout_id == payout_id)
            .order_by(PayoutAdjustment.created_at)
        )
        return list(self._session.execute(statement).scalars())

    def adjusted_payment_ids(self) -> set[uuid.UUID]:
        """Os pagamentos que ja geraram ajuste.

        Sem isto, dois fechamentos consecutivos descontariam a mesma devolucao
        duas vezes, e o artista pagaria em dobro por uma so."""
        return set(
            self._session.execute(select(PayoutAdjustment.related_payment_id)).scalars()
        )
