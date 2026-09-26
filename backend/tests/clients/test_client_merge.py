from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
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
        json={"name": name, "phone": "+353 87 111 1111"},
        headers=headers,
    )
    return response.json()["client"]["id"]


def test_merging_preserves_the_duplicate_instead_of_deleting_it(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-006: apagar quebraria agendamentos, sessões e pagamentos já
    ligados ao duplicado. Ele passa a apontar para o sobrevivente."""
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    survivor_id = _register(client, api_prefix, headers, "Aoife")
    duplicate_id = _register(client, api_prefix, headers, "Aoife Byrne")

    response = client.post(
        f"{api_prefix}/clients/merge",
        json={"duplicate_id": duplicate_id, "survivor_id": survivor_id},
        headers=headers,
    )

    assert response.status_code == 200
    session.expire_all()
    import uuid

    duplicate = session.get(Client, uuid.UUID(duplicate_id))
    assert duplicate is not None
    assert str(duplicate.merged_into_id) == survivor_id


def test_merged_client_disappears_from_the_list(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    survivor_id = _register(client, api_prefix, headers, "Aoife")
    duplicate_id = _register(client, api_prefix, headers, "Aoife Byrne")

    client.post(
        f"{api_prefix}/clients/merge",
        json={"duplicate_id": duplicate_id, "survivor_id": survivor_id},
        headers=headers,
    )

    names = [entry["name"] for entry in client.get(f"{api_prefix}/clients").json()]
    assert names == ["Aoife"]


def test_artist_cannot_merge_clients(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-006: somente proprietário e gerente unem duplicidades."""
    AccountBuilder(session).create(
        email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT
    )
    session.commit()
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    survivor_id = _register(client, api_prefix, headers, "Aoife")
    duplicate_id = _register(client, api_prefix, headers, "Aoife Byrne")

    response = client.post(
        f"{api_prefix}/clients/merge",
        json={"duplicate_id": duplicate_id, "survivor_id": survivor_id},
        headers=headers,
    )

    assert response.status_code == 403


def test_a_client_cannot_be_merged_into_itself(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    client_id = _register(client, api_prefix, headers, "Aoife")

    response = client.post(
        f"{api_prefix}/clients/merge",
        json={"duplicate_id": client_id, "survivor_id": client_id},
        headers=headers,
    )

    assert response.status_code == 422


def test_merging_an_already_merged_client_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    survivor_id = _register(client, api_prefix, headers, "Aoife")
    duplicate_id = _register(client, api_prefix, headers, "Aoife Byrne")
    third_id = _register(client, api_prefix, headers, "Aoife B")

    client.post(
        f"{api_prefix}/clients/merge",
        json={"duplicate_id": duplicate_id, "survivor_id": survivor_id},
        headers=headers,
    )
    response = client.post(
        f"{api_prefix}/clients/merge",
        json={"duplicate_id": duplicate_id, "survivor_id": third_id},
        headers=headers,
    )

    assert response.status_code == 422
