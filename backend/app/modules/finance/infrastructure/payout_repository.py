import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.models.payout import Payout


class PayoutRepository:
    """Acesso aos repasses semanais."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, payout: Payout) -> Payout:
        self._session.add(payout)
        self._session.flush()
        return payout

    def find_by_id(self, payout_id: uuid.UUID) -> Payout | None:
        return self._session.get(Payout, payout_id)

    def find_for_week(self, artist_id: uuid.UUID, period_end: datetime) -> Payout | None:
        """O fechamento daquele artista naquela semana, se ja existir.

        E o que torna o calculo sob demanda seguro: quem abre a tela duas vezes
        encontra o mesmo repasse em vez de criar outro. A garantia de verdade e
        `uq_payout_period`, no banco, porque duas abas sao dois processos."""
        statement = select(Payout).where(
            Payout.artist_id == artist_id, Payout.period_end == period_end
        )
        return self._session.execute(statement).scalars().first()

    def list_for_week(self, period_end: datetime) -> list[Payout]:
        statement = (
            select(Payout).where(Payout.period_end == period_end).order_by(Payout.created_at)
        )
        return list(self._session.execute(statement).scalars())

    def list_all(self) -> list[Payout]:
        statement = select(Payout).order_by(Payout.period_end.desc(), Payout.created_at)
        return list(self._session.execute(statement).scalars())

    def list_for_artist(self, artist_id: uuid.UUID) -> list[Payout]:
        statement = (
            select(Payout)
            .where(Payout.artist_id == artist_id)
            .order_by(Payout.period_end.desc())
        )
        return list(self._session.execute(statement).scalars())
