from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
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
    other = builder.create(email="other@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    guest = builder.create(email="guest@studio.ie", password=PASSWORD, role=UserRole.GUEST)
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    session.add(subject)
    session.flush()
    session.commit()
    return {
        "owner": str(owner.id),
        "artist": str(artist.id),
        "other": str(other.id),
        "guest": str(guest.id),
        "client": str(subject.id),
    }


def _create_bench(client: TestClient, api_prefix: str, headers: dict[str, str]) -> str:
    response = client.post(f"{api_prefix}/benches", json={"label": "Window"}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _booking_payload(client_id: str, bench_id: str, hours_offset: int = 0) -> dict:
    start = START + timedelta(hours=hours_offset)
    return {
        "client_id": client_id,
        "bench_id": bench_id,
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=2)).isoformat(),
    }


def _approved_booking(
    caller: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    payload: dict,
) -> dict:
    """Cria, confirma o sinal e aprova.

    Desde a M5 a aprovacao exige sinal confirmado (RN-AGE-005 e RN-PAG-002), e
    `approve_immediately` deixou de dar conta: nao existe sinal confirmado para
    um agendamento que ainda nao foi gravado. Os tres passos ficam aqui, num
    lugar so, em vez de repetidos em cada cenario que precisa de um agendamento
    aprovado para testar outra coisa."""
    created = caller.post(f"{api_prefix}/bookings", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    booking = created.json()

    DepositConfirmer(caller, api_prefix).confirm_for(booking["id"], headers)

    approved = caller.post(f"{api_prefix}/bookings/{booking['id']}/approve", headers=headers)
    assert approved.status_code == 200, approved.text
    return approved.json()


def test_artist_request_starts_as_pending(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-005: residente sempre cria em Solicitada."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, owner_headers)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/bookings", json=_booking_payload(ids["client"], bench_id), headers=headers
    )

    assert response.status_code == 201
    assert response.json()["status"] == "REQUESTED"


def test_artist_cannot_create_an_already_approved_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, owner_headers)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], bench_id), "approve_immediately": True},
        headers=headers,
    )

    assert response.status_code == 403


def test_management_cannot_create_an_approved_booking_before_the_deposit(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-005: criar ja aprovado vale *"desde que confirmem o sinal"*, e o
    sinal pertence ao agendamento (RN-PAG-001) -- que ainda nao existe no
    instante da criacao. Nao ha sinal confirmado a apresentar, entao o atalho e
    recusado com a instrucao do caminho certo."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)

    response = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], bench_id),
            "artist_id": ids["artist"],
            "approve_immediately": True,
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert "deposit" in response.json()["detail"].lower()


def test_management_creates_an_approved_booking_for_a_guest_own_client(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-GST-004: o guest recebe diretamente dos clientes proprios e esses
    valores nao passam pelo estudio, entao esse agendamento nao exige sinal --
    e o atalho continua aberto exatamente ali."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)

    response = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], bench_id),
            "artist_id": ids["guest"],
            "approve_immediately": True,
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "APPROVED"


def test_artist_cannot_book_on_behalf_of_another_artist(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, owner_headers)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], bench_id), "artist_id": ids["other"]},
        headers=headers,
    )

    assert response.status_code == 403


def test_artist_cannot_approve_a_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-005: apenas proprietário e gerente decidem."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, owner_headers)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    created = artist.post(
        f"{api_prefix}/bookings", json=_booking_payload(ids["client"], bench_id), headers=headers
    ).json()

    response = artist.post(f"{api_prefix}/bookings/{created['id']}/approve", headers=headers)

    assert response.status_code == 403


def test_management_approves_a_pending_request(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
        headers=headers,
    ).json()
    DepositConfirmer(client, api_prefix).confirm_for(created["id"], headers)

    response = client.post(f"{api_prefix}/bookings/{created['id']}/approve", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_approving_an_overlapping_request_returns_conflict(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-004 e RN-AGE-007: duas pendentes coexistem, mas só uma vira
    aprovada. A segunda aprovação devolve 409 para alimentar o modal."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)

    first = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
        headers=headers,
    ).json()
    second = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], bench_id, hours_offset=1),
            "artist_id": ids["other"],
        },
        headers=headers,
    ).json()

    deposits = DepositConfirmer(client, api_prefix)
    deposits.confirm_for(first["id"], headers)
    deposits.confirm_for(second["id"], headers)

    assert (
        client.post(f"{api_prefix}/bookings/{first['id']}/approve", headers=headers).status_code
        == 200
    )
    conflict = client.post(f"{api_prefix}/bookings/{second['id']}/approve", headers=headers)

    assert conflict.status_code == 409


def test_rejection_requires_one_of_the_listed_reasons(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-006: motivo de lista fechada."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
        headers=headers,
    ).json()

    invalid = client.post(
        f"{api_prefix}/bookings/{created['id']}/reject",
        json={"reason": "I do not like it"},
        headers=headers,
    )
    valid = client.post(
        f"{api_prefix}/bookings/{created['id']}/reject",
        json={"reason": "SLOT_TAKEN", "note": "Already promised"},
        headers=headers,
    )

    assert invalid.status_code == 422
    assert valid.status_code == 200
    assert valid.json()["status"] == "REJECTED"


def test_rejecting_frees_the_artist_agenda(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-014: recusado sai da agenda, preservando o registro."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
        headers=headers,
    ).json()

    client.post(
        f"{api_prefix}/bookings/{created['id']}/reject",
        json={"reason": "RESCHEDULED"},
        headers=headers,
    )
    again = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
        headers=headers,
    )

    assert again.status_code == 201


def test_cancelling_closes_the_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)
    created = _approved_booking(
        client,
        api_prefix,
        headers,
        {**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
    )

    response = client.post(
        f"{api_prefix}/bookings/{created['id']}/cancel",
        json={"reason": "Client called"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_no_show_is_recorded_separately_from_cancellation(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-010: não comparecimento é estado próprio, com retenção do sinal
    tratada pelo módulo financeiro."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)
    created = _approved_booking(
        client,
        api_prefix,
        headers,
        {**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
    )

    response = client.post(
        f"{api_prefix}/bookings/{created['id']}/cancel",
        json={"reason": "Did not arrive", "no_show": True},
        headers=headers,
    )

    assert response.json()["status"] == "NO_SHOW"


def test_artist_cannot_cancel_directly(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-008: o artista solicita à administração, não cancela."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, owner_headers)
    created = _approved_booking(
        client,
        api_prefix,
        owner_headers,
        {**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
    )

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/bookings/{created['id']}/cancel",
        json={"reason": "cannot make it"},
        headers=headers,
    )

    assert response.status_code == 403


def test_rescheduling_onto_an_occupied_slot_returns_conflict(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)

    _approved_booking(
        client,
        api_prefix,
        headers,
        {**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
    )
    movable = _approved_booking(
        client,
        api_prefix,
        headers,
        {
            **_booking_payload(ids["client"], bench_id, hours_offset=5),
            "artist_id": ids["other"],
        },
    )

    response = client.post(
        f"{api_prefix}/bookings/{movable['id']}/reschedule",
        json={
            "starts_at": START.isoformat(),
            "ends_at": (START + timedelta(hours=2)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 409


def test_artist_only_lists_their_own_bookings(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)
    client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], bench_id), "artist_id": ids["artist"]},
        headers=headers,
    )
    client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], bench_id, hours_offset=5),
            "artist_id": ids["other"],
        },
        headers=headers,
    )

    artist = TestClient(client.app)
    _sign_in(artist, api_prefix, "artist@studio.ie")

    assert len(client.get(f"{api_prefix}/bookings").json()) == 2
    own = artist.get(f"{api_prefix}/bookings").json()
    assert len(own) == 1
    assert own[0]["artist_id"] == ids["artist"]


def test_end_before_start_is_refused(client: TestClient, session: Session, api_prefix: str) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)

    response = client.post(
        f"{api_prefix}/bookings",
        json={
            "client_id": ids["client"],
            "bench_id": bench_id,
            "artist_id": ids["artist"],
            "starts_at": START.isoformat(),
            "ends_at": (START - timedelta(hours=1)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_artist_cannot_create_benches(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    _setup(session)
    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")

    response = artist.post(f"{api_prefix}/benches", json={"label": "Mine"}, headers=headers)

    assert response.status_code == 403
