import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.scheduling.infrastructure.models.bench import Bench


class BenchRepository:
    """Acesso às macas do estúdio."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, bench: Bench) -> Bench:
        self._session.add(bench)
        self._session.flush()
        return bench

    def find_by_id(self, bench_id: uuid.UUID) -> Bench | None:
        return self._session.get(Bench, bench_id)

    def list_all(self) -> list[Bench]:
        return list(self._session.execute(select(Bench).order_by(Bench.number)).scalars())

    def list_active(self) -> list[Bench]:
        statement = select(Bench).where(Bench.active.is_(True)).order_by(Bench.number)
        return list(self._session.execute(statement).scalars())

    def next_number(self) -> int:
        current = self._session.execute(select(func.max(Bench.number))).scalar_one_or_none()
        return (current or 0) + 1
