from fastapi.testclient import TestClient
from sqlalchemy import text
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


def test_registering_a_client_requires_name_and_phone(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    missing_phone = client.post(
        f"{api_prefix}/clients", json={"name": "Aoife"}, headers=headers
    )
    complete = client.post(
        f"{api_prefix}/clients",
        json={"name": "Aoife", "phone": "+353 87 111 1111"},
        headers=headers,
    )

    assert missing_phone.status_code == 422
    assert complete.status_code == 201
    assert complete.json()["client"]["instagram"] is None


def test_duplicate_phone_is_warned_but_not_blocked(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-005: alerta sem bloquear. Duas pessoas podem legitimamente
    compartilhar um telefone."""
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    payload = {"name": "Aoife", "phone": "+353 87 111 1111"}

    first = client.post(f"{api_prefix}/clients", json=payload, headers=headers)
    second = client.post(
        f"{api_prefix}/clients", json={**payload, "name": "Aoife Byrne"}, headers=headers
    )

    assert first.json()["possible_duplicates"] == []
    assert second.status_code == 201
    duplicates = second.json()["possible_duplicates"]
    assert len(duplicates) == 1
    assert duplicates[0]["name"] == "Aoife"


def test_duplicate_instagram_is_warned(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    client.post(
        f"{api_prefix}/clients",
        json={"name": "Aoife", "phone": "+353 87 111 1111", "instagram": "@aoife"},
        headers=headers,
    )
    second = client.post(
        f"{api_prefix}/clients",
        json={"name": "Aoife B", "phone": "+353 87 222 2222", "instagram": "@aoife"},
        headers=headers,
    )

    assert len(second.json()["possible_duplicates"]) == 1


def test_registration_is_audited(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    client.post(
        f"{api_prefix}/clients",
        json={"name": "Aoife", "phone": "+353 87 111 1111"},
        headers=headers,
    )

    recorded = session.execute(
        text("SELECT count(*) FROM audit_log WHERE action = 'CLIENT_REGISTERED'")
    ).scalar_one()
    assert recorded == 1


def test_registering_without_csrf_header_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/clients", json={"name": "Aoife", "phone": "+353 87 111 1111"}
    )

    assert response.status_code == 403


def test_unauthenticated_request_is_refused(client: TestClient, api_prefix: str) -> None:
    assert client.get(f"{api_prefix}/clients").status_code == 401


def test_guest_can_register_a_client_for_their_own_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-001: o guest informa os dados básicos na própria reserva."""
    AccountBuilder(session).create(
        email="guest@studio.ie", password=PASSWORD, role=UserRole.GUEST
    )
    session.commit()
    headers = _sign_in(client, api_prefix, "guest@studio.ie")

    response = client.post(
        f"{api_prefix}/clients",
        json={"name": "Aoife", "phone": "+353 87 111 1111"},
        headers=headers,
    )

    assert response.status_code == 201
