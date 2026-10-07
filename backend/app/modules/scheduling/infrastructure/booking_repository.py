import uuid
from datetime import datetime

from psycopg.types.range import Range
from sqlalchemy import Select, select, text
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
        "booking_bench_no_overlap": "bench",
        "booking_artist_no_overlap": "artist",
    }

    _CONFLICT_MESSAGE = {
        "bench": "This bench is already booked for an overlapping period.",
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

    def list_for_artist(
        self,
        artist_id: uuid.UUID,
        window: Range | None = None,
        status: BookingStatus | None = None,
    ) -> list[Booking]:
        statement = select(Booking).where(Booking.artist_id == artist_id)
        return self._fetch(statement, window, status)

    def list_all(
        self, window: Range | None = None, status: BookingStatus | None = None
    ) -> list[Booking]:
        return self._fetch(select(Booking), window, status)

    def _fetch(
        self,
        statement: Select[tuple[Booking]],
        window: Range | None,
        status: BookingStatus | None = None,
    ) -> list[Booking]:
        """Aplica a janela de tempo, quando houver, e ordena.

        O recorte usa o operador de sobreposicao do PostgreSQL, `&&`, e nao uma
        comparacao com o inicio do agendamento: uma sessao que comeca as 19h de
        terca e termina as 21h **pertence** ao dia de terca, e um filtro por
        `inicio >= :de` a perderia ao consultar so a partir das 20h.

        Sem janela, devolve tudo. A agenda sempre informa uma; quem nao informa
        esta consultando historico, e ai o conjunto inteiro e o que se quer.

        O filtro por estado existe para a pergunta que o painel do gestor faz: as
        solicitacoes esperando decisao, sem janela de data (RN-AGE-012). Sem ele,
        perguntar isso traria o historico inteiro do estudio para o navegador
        filtrar -- custo que cresce toda semana sem ninguem ter mudado nada."""
        if window is not None:
            statement = statement.where(Booking.period.op("&&")(window))
        if status is not None:
            statement = statement.where(Booking.status == status)
        ordered = statement.order_by(Booking.requested_at.desc())
        return list(self._session.execute(ordered).scalars())

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
        column = "bench_id" if scope == "bench" else "artist_id"
        statuses = (
            "('APPROVED')" if scope == "bench" else "('REQUESTED', 'APPROVED')"
        )
        self._session.rollback()
        found = self._session.execute(
            text(
                f"SELECT id FROM booking WHERE {column} = :owner"  # noqa: S608 - coluna de lista fixa
                f" AND status IN {statuses} AND period && CAST(:period AS tstzrange) LIMIT 1"
            ),
            {
                "owner": booking.bench_id if scope == "bench" else booking.artist_id,
                "period": self._period_literal(booking),
            },
        ).scalar_one_or_none()
        return str(found) if found else None

    @staticmethod
    def _period_literal(booking: Booking) -> str:
        period = booking.period
        return f"[{period.lower.isoformat()},{period.upper.isoformat()})"
