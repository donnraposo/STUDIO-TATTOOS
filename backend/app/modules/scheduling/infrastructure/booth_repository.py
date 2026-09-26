import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.scheduling.infrastructure.models.booth import Booth


class BoothRepository:
    """Acesso às macas do estúdio."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, booth: Booth) -> Booth:
        self._session.add(booth)
        self._session.flush()
        return booth

    def find_by_id(self, booth_id: uuid.UUID) -> Booth | None:
        return self._session.get(Booth, booth_id)

    def list_all(self) -> list[Booth]:
        return list(self._session.execute(select(Booth).order_by(Booth.number)).scalars())

    def list_active(self) -> list[Booth]:
        statement = select(Booth).where(Booth.active.is_(True)).order_by(Booth.number)
        return list(self._session.execute(statement).scalars())

    def next_number(self) -> int:
        current = self._session.execute(select(func.max(Booth.number))).scalar_one_or_none()
        return (current or 0) + 1
