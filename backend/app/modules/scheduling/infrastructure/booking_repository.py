import uuid
from datetime import datetime

from psycopg.types.range import Range
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.scheduling.domain.booking_status import BookingStatus
from app.modules.scheduling.infrastructure.models.booking import Booking
from app.shared.errors.booking_conflict_error import BookingConflictError


class BookingRepository:
    """Acesso aos agendamentos.

    O ponto central é `persist`: as restrições `EXCLUDE` do banco recusam
    sobreposição, e é aqui que a violação vira um erro de domínio com o
    agendamento conflitante junto — o que a RN-AGE-007 exige para o modal."""

    _CONSTRAINT_SCOPE = {
        "booking_booth_no_overlap": "booth",
        "booking_artist_no_overlap": "artist",
    }

    _CONFLICT_MESSAGE = {
        "booth": "This booth is already booked for an overlapping period.",
        "artist": "This artist already has an overlapping request or booking.",
    }

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, booking: Booking) -> Booking:
        """Grava respeitando as restrições do banco.

        `flush` força a validação agora, dentro da transação, em vez de deixar o
        erro estourar no commit — assim o conflito é traduzido no lugar certo."""
        self._session.add(booking)
        try:
            self._session.flush()
        except IntegrityError as error:
            raise self._as_conflict(error, booking) from error
        return booking

    def find_by_id(self, booking_id: uuid.UUID) -> Booking | None:
        return self._session.get(Booking, booking_id)

    def list_for_artist(self, artist_id: uuid.UUID) -> list[Booking]:
        statement = (
            select(Booking)
            .where(Booking.artist_id == artist_id)
            .order_by(Booking.requested_at.desc())
        )
        return list(self._session.execute(statement).scalars())

    def list_all(self) -> list[Booking]:
        statement = select(Booking).order_by(Booking.requested_at.desc())
        return list(self._session.execute(statement).scalars())

    def list_pending(self) -> list[Booking]:
        statement = (
            select(Booking)
            .where(Booking.status == BookingStatus.REQUESTED)
            .order_by(Booking.requested_at)
        )
        return list(self._session.execute(statement).scalars())

    @staticmethod
    def build_period(starts_at: datetime, ends_at: datetime) -> Range:
        """Intervalo fechado no início e aberto no fim.

        É o que permite um agendamento terminar 12h e o seguinte começar 12h na
        mesma maca sem colidir, atendendo à RN-AGE-001, que não prevê pausa
        obrigatória."""
        return Range(starts_at, ends_at, bounds="[)")

    def _as_conflict(self, error: IntegrityError, booking: Booking) -> BookingConflictError:
        raw = str(error.orig)
        for constraint, scope in self._CONSTRAINT_SCOPE.items():
            if constraint in raw:
                return BookingConflictError(
                    scope=scope,
                    message=self._CONFLICT_MESSAGE[scope],
                    conflicting_booking_id=self._find_conflicting_id(booking, scope),
                )
        raise error

    def _find_conflicting_id(self, booking: Booking, scope: str) -> str | None:
        """Busca o agendamento que causou o choque, para alimentar o modal.

        A transação está abortada após a violação, então a consulta roda em
        `SAVEPOINT` próprio; sem isso o PostgreSQL recusaria qualquer comando."""
        column = "booth_id" if scope == "booth" else "artist_id"
        statuses = (
            "('APPROVED')" if scope == "booth" else "('REQUESTED', 'APPROVED')"
        )
        self._session.rollback()
        found = self._session.execute(
            text(
                f"SELECT id FROM booking WHERE {column} = :owner"  # noqa: S608 - coluna de lista fixa
                f" AND status IN {statuses} AND period && CAST(:period AS tstzrange) LIMIT 1"
            ),
            {
                "owner": booking.booth_id if scope == "booth" else booking.artist_id,
                "period": self._period_literal(booking),
            },
        ).scalar_one_or_none()
        return str(found) if found else None

    @staticmethod
    def _period_literal(booking: Booking) -> str:
        period = booking.period
        return f"[{period.lower.isoformat()},{period.upper.isoformat()})"
