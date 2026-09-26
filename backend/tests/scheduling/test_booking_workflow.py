from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from tests.support.account_builder import AccountBuilder

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
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    session.add(subject)
    session.flush()
    session.commit()
    return {
        "owner": str(owner.id),
        "artist": str(artist.id),
        "other": str(other.id),
        "client": str(subject.id),
    }


def _create_booth(client: TestClient, api_prefix: str, headers: dict[str, str]) -> str:
    response = client.post(f"{api_prefix}/booths", json={"label": "Window"}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _booking_payload(client_id: str, booth_id: str, hours_offset: int = 0) -> dict:
    start = START + timedelta(hours=hours_offset)
    return {
        "client_id": client_id,
        "booth_id": booth_id,
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=2)).isoformat(),
    }


def test_artist_request_starts_as_pending(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-005: residente sempre cria em Solicitada."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _create_booth(client, api_prefix, owner_headers)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/bookings", json=_booking_payload(ids["client"], booth_id), headers=headers
    )

    assert response.status_code == 201
    assert response.json()["status"] == "REQUESTED"


def test_artist_cannot_create_an_already_approved_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _create_booth(client, api_prefix, owner_headers)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], booth_id), "approve_immediately": True},
        headers=headers,
    )

    assert response.status_code == 403


def test_management_can_create_an_approved_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _create_booth(client, api_prefix, headers)

    response = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], booth_id),
            "artist_id": ids["artist"],
            "approve_immediately": True,
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "APPROVED"


def test_artist_cannot_book_on_behalf_of_another_artist(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _create_booth(client, api_prefix, owner_headers)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], booth_id), "artist_id": ids["other"]},
        headers=headers,
    )

    assert response.status_code == 403


def test_artist_cannot_approve_a_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-005: apenas proprietário e gerente decidem."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _create_booth(client, api_prefix, owner_headers)

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    created = artist.post(
        f"{api_prefix}/bookings", json=_booking_payload(ids["client"], booth_id), headers=headers
    ).json()

    response = artist.post(f"{api_prefix}/bookings/{created['id']}/approve", headers=headers)

    assert response.status_code == 403


def test_management_approves_a_pending_request(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _create_booth(client, api_prefix, headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], booth_id), "artist_id": ids["artist"]},
        headers=headers,
    ).json()

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
    booth_id = _create_booth(client, api_prefix, headers)

    first = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], booth_id), "artist_id": ids["artist"]},
        headers=headers,
    ).json()
    second = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], booth_id, hours_offset=1),
            "artist_id": ids["other"],
        },
        headers=headers,
    ).json()

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
    booth_id = _create_booth(client, api_prefix, headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], booth_id), "artist_id": ids["artist"]},
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
    booth_id = _create_booth(client, api_prefix, headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], booth_id), "artist_id": ids["artist"]},
        headers=headers,
    ).json()

    client.post(
        f"{api_prefix}/bookings/{created['id']}/reject",
        json={"reason": "RESCHEDULED"},
        headers=headers,
    )
    again = client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], booth_id), "artist_id": ids["artist"]},
        headers=headers,
    )

    assert again.status_code == 201


def test_cancelling_closes_the_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _create_booth(client, api_prefix, headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], booth_id),
            "artist_id": ids["artist"],
            "approve_immediately": True,
        },
        headers=headers,
    ).json()

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
    booth_id = _create_booth(client, api_prefix, headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], booth_id),
            "artist_id": ids["artist"],
            "approve_immediately": True,
        },
        headers=headers,
    ).json()

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
    booth_id = _create_booth(client, api_prefix, owner_headers)
    created = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], booth_id),
            "artist_id": ids["artist"],
            "approve_immediately": True,
        },
        headers=owner_headers,
    ).json()

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
    booth_id = _create_booth(client, api_prefix, headers)

    client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], booth_id),
            "artist_id": ids["artist"],
            "approve_immediately": True,
        },
        headers=headers,
    )
    movable = client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], booth_id, hours_offset=5),
            "artist_id": ids["other"],
            "approve_immediately": True,
        },
        headers=headers,
    ).json()

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
    booth_id = _create_booth(client, api_prefix, headers)
    client.post(
        f"{api_prefix}/bookings",
        json={**_booking_payload(ids["client"], booth_id), "artist_id": ids["artist"]},
        headers=headers,
    )
    client.post(
        f"{api_prefix}/bookings",
        json={
            **_booking_payload(ids["client"], booth_id, hours_offset=5),
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
    booth_id = _create_booth(client, api_prefix, headers)

    response = client.post(
        f"{api_prefix}/bookings",
        json={
            "client_id": ids["client"],
            "booth_id": booth_id,
            "artist_id": ids["artist"],
            "starts_at": START.isoformat(),
            "ends_at": (START - timedelta(hours=1)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_artist_cannot_create_booths(client: TestClient, session: Session, api_prefix: str) -> None:
    _setup(session)
    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")

    response = artist.post(f"{api_prefix}/booths", json={"label": "Mine"}, headers=headers)

    assert response.status_code == 403
