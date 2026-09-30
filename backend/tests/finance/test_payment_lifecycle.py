"""Ciclo do pagamento pela API (RN-PAG-002, RN-PAG-006, RN-PAG-007 e RN-PAG-009).

O que mais importa aqui e o **portao da RN-AGE-005**: uma solicitacao nao pode
ser aprovada enquanto o sinal nao estiver confirmado. Informado nao basta; o
estudio precisa ter conferido o recebimento.

O segundo e a imutabilidade da RN-PAG-007: um pagamento nunca e apagado, e um
recusado nao volta a confirmado. Correcao entra como devolucao vinculada.
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from tests.support.account_builder import AccountBuilder
from tests.support.deposit_confirmer import DepositConfirmer

PASSWORD = "correct horse battery staple"
START = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _setup(session: Session) -> dict[str, str]:
    builder = AccountBuilder(session)
    owner = builder.create(email="owner@studio.ie", password=PASSWORD)
    artist = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    session.add(subject)
    session.flush()
    session.commit()
    return {
        "owner": str(owner.id),
        "artist": str(artist.id),
        "client": str(subject.id),
    }


def _booking(
    client: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    ids: dict[str, str],
    hours_offset: int = 0,
) -> str:
    bench = client.post(f"{api_prefix}/benches", json={"label": None}, headers=headers)
    assert bench.status_code == 201, bench.text
    start = START + timedelta(hours=hours_offset)
    created = client.post(
        f"{api_prefix}/bookings",
        json={
            "client_id": ids["client"],
            "bench_id": bench.json()["id"],
            "artist_id": ids["artist"],
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=2)).isoformat(),
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


def test_a_payment_is_born_reported(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-PAG-002: informar e confirmar sao atos diferentes."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)

    response = client.post(
        f"{api_prefix}/payments",
        json={
            "booking_id": booking_id,
            "amount": "50.00",
            "kind": "DEPOSIT",
            "method": "BANK_TRANSFER",
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "REPORTED"
    assert response.json()["confirmed_at"] is None


def test_the_artist_cannot_register_a_payment(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-PAG-006: todos os recebimentos sao inseridos e confirmados
    manualmente por gerente ou proprietario nesta versao."""
    ids = _setup(session)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, owner, ids)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/payments",
        json={
            "booking_id": booking_id,
            "amount": "50.00",
            "kind": "DEPOSIT",
            "method": "CASH",
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_a_reported_deposit_does_not_open_the_gate(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-005 e RN-PAG-002: sem **confirmacao** do pagamento, o agendamento
    nao pode ser aprovado. Informado nao basta."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    DepositConfirmer(client, api_prefix).register_for(booking_id, headers)

    response = client.post(f"{api_prefix}/bookings/{booking_id}/approve", headers=headers)

    assert response.status_code == 422
    assert "deposit" in response.json()["detail"].lower()


def test_a_confirmed_deposit_opens_the_gate(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    DepositConfirmer(client, api_prefix).confirm_for(booking_id, headers)

    response = client.post(f"{api_prefix}/bookings/{booking_id}/approve", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "APPROVED"


def test_the_artist_cannot_confirm_a_payment(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Deixar o artista confirmar o proprio recebimento seria deixa-lo liberar
    o proprio pagamento."""
    ids = _setup(session)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, owner, ids)
    payment_id = DepositConfirmer(client, api_prefix).register_for(booking_id, owner)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(f"{api_prefix}/payments/{payment_id}/confirm", headers=headers)

    assert response.status_code == 403


def test_a_refused_payment_never_becomes_confirmed(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-PAG-007: o lancamento permanece no historico e nao volta atras."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    payment_id = DepositConfirmer(client, api_prefix).register_for(booking_id, headers)

    refused = client.post(
        f"{api_prefix}/payments/{payment_id}/refuse",
        json={"reason": "The transfer never landed."},
        headers=headers,
    )
    again = client.post(f"{api_prefix}/payments/{payment_id}/confirm", headers=headers)

    assert refused.status_code == 200, refused.text
    assert refused.json()["status"] == "REFUSED"
    assert again.status_code == 422


def test_a_refused_deposit_lets_the_client_pay_another(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O indice parcial so conta sinal vivo: recusado sai da conta."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    deposits = DepositConfirmer(client, api_prefix)
    first = deposits.register_for(booking_id, headers)
    client.post(
        f"{api_prefix}/payments/{first}/refuse",
        json={"reason": "Wrong amount."},
        headers=headers,
    )

    second = deposits.confirm_for(booking_id, headers)

    assert second != first
    approved = client.post(f"{api_prefix}/bookings/{booking_id}/approve", headers=headers)
    assert approved.status_code == 200, approved.text


def test_two_live_deposits_cannot_coexist(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-PAG-001: um sinal por agendamento. A garantia e do banco."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    DepositConfirmer(client, api_prefix).confirm_for(booking_id, headers)

    duplicated = client.post(
        f"{api_prefix}/payments",
        json={
            "booking_id": booking_id,
            "amount": "50.00",
            "kind": "DEPOSIT",
            "method": "CASH",
        },
        headers=headers,
    )

    assert duplicated.status_code == 422
    assert "deposit" in duplicated.json()["detail"].lower()


def test_a_deposit_belongs_to_a_booking_not_to_a_session(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/payments",
        json={"amount": "50.00", "kind": "DEPOSIT", "method": "CASH"},
        headers=headers,
    )

    assert response.status_code == 422


def test_cancelling_retains_the_deposit(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-009: o sinal fica com o estudio, mesmo com aviso de 24 horas.

    Retido continua confirmado -- o dinheiro nao voltou. O que muda e que ele
    deixa de valer como sinal daquele horario."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    payment_id = DepositConfirmer(client, api_prefix).confirm_for(booking_id, headers)
    client.post(f"{api_prefix}/bookings/{booking_id}/approve", headers=headers)

    client.post(
        f"{api_prefix}/bookings/{booking_id}/cancel",
        json={"reason": "Client called"},
        headers=headers,
    )

    payments = client.get(f"{api_prefix}/bookings/{booking_id}/payments", headers=headers).json()
    deposit = next(payment for payment in payments if payment["id"] == payment_id)
    assert deposit["status"] == "CONFIRMED"
    assert deposit["retained_at"] is not None
    assert deposit["retained_reason"]


def test_rejecting_leaves_the_deposit_to_be_returned(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-PAG-003: recusa pelo estudio devolve o sinal integralmente. O sistema
    aponta o que deve voltar; quem registra a devolucao e o gestor, depois de
    realiza-la (RN-PAG-009)."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    payment_id = DepositConfirmer(client, api_prefix).confirm_for(booking_id, headers)

    client.post(
        f"{api_prefix}/bookings/{booking_id}/reject",
        json={"reason": "STUDIO_CLOSED"},
        headers=headers,
    )

    payments = client.get(f"{api_prefix}/bookings/{booking_id}/payments", headers=headers).json()
    deposit = next(payment for payment in payments if payment["id"] == payment_id)
    assert deposit["retained_at"] is None

    awaiting = session.execute(
        text(
            "SELECT new_values FROM audit_log"
            " WHERE action = 'BOOKING_SETTLED' AND entity_id = :id"
        ),
        {"id": booking_id},
    ).scalar_one()
    assert payment_id in awaiting["awaiting_refund"]


def test_the_manager_registers_the_refund_manually(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-PAG-009: a devolucao e registrada depois de realizada, com forma
    propria -- que pode diferir da forma do pagamento original."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    payment_id = DepositConfirmer(client, api_prefix).confirm_for(booking_id, headers)

    response = client.post(
        f"{api_prefix}/payments/{payment_id}/refund",
        json={
            "amount": "50.00",
            "method": "CASH",
            "reason": "The studio rejected the request.",
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["method"] == "CASH"
    payments = client.get(f"{api_prefix}/bookings/{booking_id}/payments", headers=headers).json()
    assert payments[0]["status"] == "REFUNDED"


def test_a_refund_cannot_exceed_what_came_in(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, headers, ids)
    payment_id = DepositConfirmer(client, api_prefix).confirm_for(booking_id, headers)

    response = client.post(
        f"{api_prefix}/payments/{payment_id}/refund",
        json={"amount": "80.00", "method": "CASH", "reason": "Too much."},
        headers=headers,
    )

    assert response.status_code == 422


def test_the_artist_sees_the_payments_of_their_own_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-007: e do recebimento que sai o repasse dele."""
    ids = _setup(session)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    booking_id = _booking(client, api_prefix, owner, ids)
    DepositConfirmer(client, api_prefix).confirm_for(booking_id, owner)

    artist = TestClient(client.app)
    _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.get(f"{api_prefix}/bookings/{booking_id}/payments")

    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
