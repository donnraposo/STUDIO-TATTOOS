"""Prova das garantias de banco do orçamento e da sessão (migração `0005`).

Como os testes da M3.1, estes escrevem SQL direto, sem passar por caso de uso: o
que se verifica é a garantia do banco. Um caso de uso pode ser reescrito, e
outro pode ser acrescentado amanhã esquecendo uma regra; a restrição continua
valendo para os dois.

A escolha do que travar no banco não foi por gosto. Cada restrição aqui protege
um erro que só apareceria muito depois, no dinheiro de alguém: orçamento
aprovado sem percentual congelado só se revela no repasse; sessão parcial sem
valor cobrado, no cálculo do que o artista deveria receber.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from app.modules.scheduling.infrastructure.models.bench import Bench
from tests.support.account_builder import AccountBuilder

PERFORMED_AT = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)


def _insert(session: Session, table: str, values: dict[str, object]) -> None:
    columns = ", ".join(values)
    parameters = ", ".join(f":{name}" for name in values)
    session.execute(text(f"INSERT INTO {table} ({columns}) VALUES ({parameters})"), values)


def _insert_quote(
    session: Session, fx: dict[str, uuid.UUID], **overrides: object
) -> uuid.UUID:
    quote_id = uuid.uuid4()
    values: dict[str, object] = {
        "id": quote_id,
        "client_id": fx["client"],
        "artist_id": fx["artist"],
        "created_by": fx["manager"],
        "origin": "ARTIST_OWN",
        "description": "Blackwork forearm sleeve",
        "body_region": "Left forearm",
        "size_estimate": "20cm",
        "total_value": Decimal("1000.00"),
        "planned_sessions": 4,
        "planned_value_per_session": Decimal("250.00"),
        "estimated_duration_minutes": 180,
        "status": "PENDING",
    }
    values.update(overrides)
    _insert(session, "quote", values)
    return quote_id


def _insert_session(
    session: Session, quote_id: uuid.UUID, **overrides: object
) -> uuid.UUID:
    session_id = uuid.uuid4()
    values: dict[str, object] = {
        "id": session_id,
        "quote_id": quote_id,
        "sequence_number": 1,
        "status": "SCHEDULED",
        "origin": "ARTIST_OWN",
        "planned_value": Decimal("250.00"),
        "artist_percentage": Decimal("70.00"),
    }
    values.update(overrides)
    _insert(session, "tattoo_session", values)
    return session_id


def _insert_booking(
    session: Session,
    fx: dict[str, uuid.UUID],
    session_id: uuid.UUID | None,
    status: str = "APPROVED",
    bench: str = "bench_one",
    start: datetime = PERFORMED_AT,
) -> uuid.UUID:
    booking_id = uuid.uuid4()
    period = f"[{start.isoformat()},{(start + timedelta(hours=2)).isoformat()})"
    session.execute(
        text(
            "INSERT INTO booking (id, client_id, artist_id, bench_id, period, status, session_id)"
            " VALUES (:id, :client, :artist, :bench, CAST(:period AS tstzrange), :status,"
            " :session_id)"
        ),
        {
            "id": booking_id,
            "client": fx["client"],
            "artist": fx["artist"],
            "bench": fx[bench],
            "period": period,
            "status": status,
            "session_id": session_id,
        },
    )
    return booking_id


@pytest.fixture
def quote_fixtures(session: Session) -> dict[str, uuid.UUID]:
    builder = AccountBuilder(session)
    artist = builder.create(email="artist@studio.ie", role=UserRole.RESIDENT)
    manager = builder.create(email="manager@studio.ie", role=UserRole.MANAGER)

    bench_one = Bench(number=1)
    bench_two = Bench(number=2)
    client = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    session.add_all([bench_one, bench_two, client])
    session.flush()
    session.commit()

    return {
        "artist": artist.id,
        "manager": manager.id,
        "client": client.id,
        "bench_one": bench_one.id,
        "bench_two": bench_two.id,
    }


def test_approved_quote_cannot_exist_without_a_frozen_percentage(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-REP-006: aprovar e congelar o percentual são o mesmo ato.

    Se este registro passasse, o repasse seria calculado meses depois com o
    percentual vigente na data do cálculo, não com o acordado na aprovação."""
    with pytest.raises(IntegrityError, match="ck_quote_approved_freezes_percentage"):
        _insert_quote(
            session,
            quote_fixtures,
            status="APPROVED",
            approved_at=PERFORMED_AT,
            approved_by=quote_fixtures["manager"],
        )
        session.flush()


def test_approved_quote_with_percentage_and_decision_is_accepted(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """O caminho positivo da mesma restrição: aprovação completa entra."""
    _insert_quote(
        session,
        quote_fixtures,
        status="APPROVED",
        artist_percentage=Decimal("70.00"),
        approved_at=PERFORMED_AT,
        approved_by=quote_fixtures["manager"],
    )
    session.flush()

    stored = session.execute(
        text("SELECT artist_percentage FROM quote WHERE status = 'APPROVED'")
    ).scalar_one()
    assert stored == Decimal("70.00")


def test_rejected_quote_requires_a_reason(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-ORC-003: a rejeição exige motivo; a observação continua opcional."""
    with pytest.raises(IntegrityError, match="ck_quote_rejected_needs_reason"):
        _insert_quote(session, quote_fixtures, status="REJECTED")
        session.flush()


def test_session_sequence_is_unique_within_the_quote(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """Duas sessões número 1 no mesmo orçamento tornariam a ordem ambígua, e a
    ordem é o que liga cada sinal de €50 à sua sessão."""
    quote_id = _insert_quote(session, quote_fixtures)
    _insert_session(session, quote_id, sequence_number=1)
    session.flush()

    with pytest.raises(IntegrityError, match="uq_tattoo_session_sequence"):
        _insert_session(session, quote_id, sequence_number=1)
        session.flush()


def test_the_same_sequence_number_is_free_in_another_quote(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """A unicidade é por orçamento: todo orçamento tem a sua sessão 1."""
    first = _insert_quote(session, quote_fixtures)
    second = _insert_quote(session, quote_fixtures)
    _insert_session(session, first, sequence_number=1)
    _insert_session(session, second, sequence_number=1)
    session.flush()

    total = session.execute(text("SELECT count(*) FROM tattoo_session")).scalar_one()
    assert total == 2


def test_partially_done_session_requires_the_charged_value(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-ORC-006: o repasse parcial é calculado sobre o valor efetivamente
    recebido. Sem esse valor gravado, não há sobre o que calcular."""
    quote_id = _insert_quote(session, quote_fixtures)

    with pytest.raises(IntegrityError, match="ck_tattoo_session_partial_requires_charged"):
        _insert_session(
            session, quote_id, status="PARTIALLY_DONE", performed_at=PERFORMED_AT
        )
        session.flush()


def test_performed_session_requires_the_real_date(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-POS-001: o vencimento do pós-venda em 15 dias conta da data real."""
    quote_id = _insert_quote(session, quote_fixtures)

    with pytest.raises(IntegrityError, match="ck_tattoo_session_performed_requires_date"):
        _insert_session(session, quote_id, status="DONE")
        session.flush()


def test_paid_off_session_requires_manager_confirmation(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """RN-ORC-005: só entra em repasse o que o gestor confirmou como recebido.

    O artista marca realizada; quitada é decisão do gestor. Um único estado para
    as duas coisas colocaria trabalho não pago no repasse de sexta."""
    quote_id = _insert_quote(session, quote_fixtures)

    with pytest.raises(IntegrityError, match="ck_tattoo_session_paid_off_requires_confirmation"):
        _insert_session(
            session,
            quote_id,
            status="PAID_OFF",
            performed_at=PERFORMED_AT,
            charged_value=Decimal("250.00"),
        )
        session.flush()


def test_a_session_cannot_have_two_live_bookings(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """A mesma sessão em dois horários seria a mesma sessão executada duas vezes.

    Os dois agendamentos estão em macas e horários diferentes de propósito: sem
    sobreposição, as restrições `EXCLUDE` da `0004` não têm o que recusar, e o
    que rejeita é o índice da sessão."""
    quote_id = _insert_quote(session, quote_fixtures)
    session_id = _insert_session(session, quote_id)
    _insert_booking(session, quote_fixtures, session_id, status="APPROVED")
    session.flush()

    with pytest.raises(IntegrityError, match="uq_booking_live_session"):
        _insert_booking(
            session,
            quote_fixtures,
            session_id,
            status="REQUESTED",
            bench="bench_two",
            start=PERFORMED_AT + timedelta(days=1),
        )
        session.flush()


def test_a_cancelled_booking_frees_the_session_for_a_new_one(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """Pelo mesmo critério da RN-AGE-014: cancelado e recusado saem da conta.

    Se não saíssem, uma sessão cancelada ficaria impossível de reagendar — e
    remarcar é justamente o caso comum."""
    quote_id = _insert_quote(session, quote_fixtures)
    session_id = _insert_session(session, quote_id)
    _insert_booking(session, quote_fixtures, session_id, status="CANCELLED")
    _insert_booking(session, quote_fixtures, session_id, status="REJECTED")
    _insert_booking(
        session,
        quote_fixtures,
        session_id,
        status="APPROVED",
        start=PERFORMED_AT + timedelta(days=1),
    )
    session.flush()

    live = session.execute(
        text(
            "SELECT count(*) FROM booking WHERE session_id = :id"
            " AND status IN ('REQUESTED', 'APPROVED')"
        ),
        {"id": session_id},
    ).scalar_one()
    assert live == 1


def test_bookings_without_a_session_are_not_limited_by_the_index(
    session: Session, quote_fixtures: dict[str, uuid.UUID]
) -> None:
    """O índice é parcial: agendamento sem orçamento ligado não entra nele.

    Toda a agenda entregue na M3 grava `session_id` nulo, e o cenário negativo
    aqui é o índice ter sido escrito sem o `WHERE`, o que travaria o segundo
    agendamento solto do estúdio."""
    _insert_booking(session, quote_fixtures, None, status="APPROVED")
    _insert_booking(
        session,
        quote_fixtures,
        None,
        status="APPROVED",
        bench="bench_two",
        start=PERFORMED_AT + timedelta(days=1),
    )
    session.flush()

    total = session.execute(
        text("SELECT count(*) FROM booking WHERE session_id IS NULL")
    ).scalar_one()
    assert total == 2
