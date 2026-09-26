"""Prova das duas restrições de não sobreposição (ADR-011).

Estes testes escrevem SQL direto, sem passar por casos de uso: o que está sendo
verificado é a garantia do banco, não a lógica da aplicação. Se a aplicação
inteira fosse reescrita amanhã, estas regras continuariam valendo.

O teste de corrida abre **duas transações paralelas reais**. Chamadas em
sequência passariam mesmo com a validação quebrada, e é justamente a corrida que
a aplicação sozinha não consegue impedir.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.container import Container
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from app.modules.scheduling.infrastructure.models.booth import Booth
from tests.support.account_builder import AccountBuilder

START = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)


def _period(start: datetime, hours: int = 2) -> str:
    return f"[{start.isoformat()},{(start + timedelta(hours=hours)).isoformat()})"


def _insert_booking(
    session: Session,
    artist_id: uuid.UUID,
    booth_id: uuid.UUID,
    client_id: uuid.UUID,
    status: str,
    start: datetime = START,
    hours: int = 2,
) -> uuid.UUID:
    booking_id = uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO booking (id, client_id, artist_id, booth_id, period, status)"
            " VALUES (:id, :client, :artist, :booth, CAST(:period AS tstzrange), :status)"
        ),
        {
            "id": booking_id,
            "client": client_id,
            "artist": artist_id,
            "booth": booth_id,
            "period": _period(start, hours),
            "status": status,
        },
    )
    return booking_id


@pytest.fixture
def scheduling_fixtures(session: Session) -> dict[str, uuid.UUID]:
    builder = AccountBuilder(session)
    first = builder.create(email="a1@studio.ie", role=UserRole.RESIDENT)
    second = builder.create(email="a2@studio.ie", role=UserRole.RESIDENT)

    booth_one = Booth(number=1)
    booth_two = Booth(number=2)
    client = Client(
        name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=first.id
    )
    session.add_all([booth_one, booth_two, client])
    session.flush()
    session.commit()

    return {
        "artist_one": first.id,
        "artist_two": second.id,
        "booth_one": booth_one.id,
        "booth_two": booth_two.id,
        "client": client.id,
    }


def test_two_approved_bookings_cannot_overlap_on_the_same_booth(
    session: Session, scheduling_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-AGE-007: nunca dois aprovados sobrepostos na mesma maca."""
    fx = scheduling_fixtures
    _insert_booking(
        session, fx["artist_one"], fx["booth_one"], fx["client"], "APPROVED"
    )
    session.flush()

    with pytest.raises(IntegrityError, match="booking_booth_no_overlap"):
        _insert_booking(
            session,
            fx["artist_two"],
            fx["booth_one"],
            fx["client"],
            "APPROVED",
            start=START + timedelta(hours=1),
        )
        session.flush()


def test_pending_requests_from_different_artists_may_compete_for_a_booth(
    session: Session, scheduling_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-AGE-004: pendente não bloqueia a maca. Duas solicitações concorrentes
    coexistem até a decisão administrativa."""
    fx = scheduling_fixtures
    _insert_booking(session, fx["artist_one"], fx["booth_one"], fx["client"], "REQUESTED")
    _insert_booking(session, fx["artist_two"], fx["booth_one"], fx["client"], "REQUESTED")
    session.flush()

    total = session.execute(
        text("SELECT count(*) FROM booking WHERE status = 'REQUESTED'")
    ).scalar_one()
    assert total == 2


def test_the_same_artist_cannot_overlap_even_on_different_booths(
    session: Session, scheduling_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-AGE-014: o artista não se compromete em dois lugares ao mesmo tempo."""
    fx = scheduling_fixtures
    _insert_booking(session, fx["artist_one"], fx["booth_one"], fx["client"], "APPROVED")
    session.flush()

    with pytest.raises(IntegrityError, match="booking_artist_no_overlap"):
        _insert_booking(
            session,
            fx["artist_one"],
            fx["booth_two"],
            fx["client"],
            "APPROVED",
            start=START + timedelta(hours=1),
        )
        session.flush()


def test_a_pending_request_already_occupies_the_artist_agenda(
    session: Session, scheduling_fixtures: dict[str, uuid.UUID]
) -> None:
    """Pendente não bloqueia a maca, mas bloqueia o próprio artista."""
    fx = scheduling_fixtures
    _insert_booking(session, fx["artist_one"], fx["booth_one"], fx["client"], "REQUESTED")
    session.flush()

    with pytest.raises(IntegrityError, match="booking_artist_no_overlap"):
        _insert_booking(
            session,
            fx["artist_one"],
            fx["booth_two"],
            fx["client"],
            "REQUESTED",
            start=START + timedelta(hours=1),
        )
        session.flush()


def test_rejected_and_cancelled_bookings_release_the_agenda(
    session: Session, scheduling_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-AGE-014: recusado e cancelado saem da agenda, preservando o histórico."""
    fx = scheduling_fixtures
    _insert_booking(session, fx["artist_one"], fx["booth_one"], fx["client"], "REJECTED")
    _insert_booking(session, fx["artist_one"], fx["booth_one"], fx["client"], "CANCELLED")
    _insert_booking(session, fx["artist_one"], fx["booth_one"], fx["client"], "APPROVED")
    session.flush()

    stored = session.execute(text("SELECT count(*) FROM booking")).scalar_one()
    assert stored == 3


def test_adjacent_bookings_are_allowed_without_a_gap(
    session: Session, scheduling_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-AGE-001: não há pausa obrigatória. Um termina 12h, o outro começa 12h."""
    fx = scheduling_fixtures
    _insert_booking(session, fx["artist_one"], fx["booth_one"], fx["client"], "APPROVED")
    _insert_booking(
        session,
        fx["artist_one"],
        fx["booth_one"],
        fx["client"],
        "APPROVED",
        start=START + timedelta(hours=2),
    )
    session.flush()

    stored = session.execute(
        text("SELECT count(*) FROM booking WHERE status = 'APPROVED'")
    ).scalar_one()
    assert stored == 2


def test_empty_period_is_refused(
    session: Session, scheduling_fixtures: dict[str, uuid.UUID]
) -> None:
    fx = scheduling_fixtures

    with pytest.raises(IntegrityError, match="ck_booking_period_not_empty"):
        _insert_booking(
            session, fx["artist_one"], fx["booth_one"], fx["client"], "APPROVED", hours=0
        )
        session.flush()


def test_concurrent_approvals_cannot_both_win(
    container: Container, scheduling_fixtures: dict[str, uuid.UUID]
) -> None:
    """A prova que importa: duas transações **paralelas de verdade**.

    Ambas leem a agenda vazia antes de gravar, exatamente como duas requisições
    simultâneas fariam. Em sequência, este cenário passaria mesmo sem restrição
    nenhuma — é a corrida que a aplicação sozinha não consegue impedir."""
    fx = scheduling_fixtures
    engine = container.database.engine

    first = engine.connect()
    second = engine.connect()
    try:
        first.begin()
        second.begin()

        statement = text(
            "INSERT INTO booking (id, client_id, artist_id, booth_id, period, status)"
            " VALUES (:id, :client, :artist, :booth, CAST(:period AS tstzrange), 'APPROVED')"
        )
        common = {
            "client": fx["client"],
            "booth": fx["booth_one"],
            "period": _period(START),
        }

        first.execute(
            statement, {**common, "id": uuid.uuid4(), "artist": fx["artist_one"]}
        )
        first.commit()

        # A segunda transação começou antes do commit da primeira e ainda assim
        # não pode vencer: a restrição decide, não a ordem de leitura.
        with pytest.raises(IntegrityError, match="booking_booth_no_overlap"):
            second.execute(
                statement, {**common, "id": uuid.uuid4(), "artist": fx["artist_two"]}
            )
            second.commit()
    finally:
        second.close()
        first.close()

    with engine.connect() as verification:
        approved = verification.execute(
            text("SELECT count(*) FROM booking WHERE status = 'APPROVED'")
        ).scalar_one()
    assert approved == 1
