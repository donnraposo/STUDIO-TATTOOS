from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.identity.domain.user_role import UserRole
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(
        f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _register(client: TestClient, api_prefix: str, headers: dict[str, str], name: str) -> str:
    response = client.post(
        f"{api_prefix}/clients",
        json={"name": name, "phone": "+353 87 111 1111", "instagram": f"@{name.lower()}"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["client"]["id"]


def test_artist_sees_the_full_record_of_a_client_they_registered(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(
        email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT
    )
    session.commit()
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    client_id = _register(client, api_prefix, headers, "Aoife")

    response = client.get(f"{api_prefix}/clients/{client_id}")

    assert response.status_code == 200
    assert "registered_by_artist_id" in response.json()
    assert "created_at" in response.json()


def test_another_artist_sees_only_the_contact_details(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-004: o artista indicado recebe nome, telefone e Instagram — nunca
    a ficha completa nem o histórico anterior."""
    builder = AccountBuilder(session)
    builder.create(email="first@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    builder.create(email="second@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    session.commit()

    owner_headers = _sign_in(client, api_prefix, "first@studio.ie")
    client_id = _register(client, api_prefix, owner_headers, "Aoife")

    other = TestClient(client.app)
    _sign_in(other, api_prefix, "second@studio.ie")
    response = other.get(f"{api_prefix}/clients/{client_id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "name", "phone", "instagram"}
    assert "registered_by_artist_id" not in body
    assert "created_at" not in body


def test_management_sees_the_full_record_of_any_client(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    builder = AccountBuilder(session)
    builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    builder.create(email="manager@studio.ie", password=PASSWORD, role=UserRole.MANAGER)
    session.commit()

    artist_headers = _sign_in(client, api_prefix, "artist@studio.ie")
    client_id = _register(client, api_prefix, artist_headers, "Aoife")

    manager = TestClient(client.app)
    _sign_in(manager, api_prefix, "manager@studio.ie")
    response = manager.get(f"{api_prefix}/clients/{client_id}")

    assert response.status_code == 200
    assert "registered_by_artist_id" in response.json()


def test_listing_only_returns_clients_the_artist_registered(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    builder = AccountBuilder(session)
    builder.create(email="first@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    builder.create(email="second@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    session.commit()

    first_headers = _sign_in(client, api_prefix, "first@studio.ie")
    _register(client, api_prefix, first_headers, "Aoife")

    second = TestClient(client.app)
    second_headers = _sign_in(second, api_prefix, "second@studio.ie")
    _register(second, api_prefix, second_headers, "Brendan")

    assert [c["name"] for c in client.get(f"{api_prefix}/clients").json()] == ["Aoife"]
    assert [c["name"] for c in second.get(f"{api_prefix}/clients").json()] == ["Brendan"]


def test_management_lists_every_client(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    builder = AccountBuilder(session)
    builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    builder.create(email="owner@studio.ie", password=PASSWORD)
    session.commit()

    artist_headers = _sign_in(client, api_prefix, "artist@studio.ie")
    _register(client, api_prefix, artist_headers, "Aoife")

    owner = TestClient(client.app)
    _sign_in(owner, api_prefix, "owner@studio.ie")

    assert len(owner.get(f"{api_prefix}/clients").json()) == 1


def test_artist_cannot_edit_a_client_registered_by_someone_else(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    builder = AccountBuilder(session)
    builder.create(email="first@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    builder.create(email="second@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    session.commit()

    first_headers = _sign_in(client, api_prefix, "first@studio.ie")
    client_id = _register(client, api_prefix, first_headers, "Aoife")

    other = TestClient(client.app)
    other_headers = _sign_in(other, api_prefix, "second@studio.ie")
    response = other.put(
        f"{api_prefix}/clients/{client_id}",
        json={"name": "Hijacked", "phone": "+353 87 999 9999", "instagram": None},
        headers=other_headers,
    )

    assert response.status_code == 403
