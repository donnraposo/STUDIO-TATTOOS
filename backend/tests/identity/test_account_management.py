from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.models.user_account import UserAccount
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _new_account_payload(role: str = "RESIDENT", email: str = "new@studio.ie") -> dict:
    return {
        "email": email,
        "password": "a-long-enough-password",
        "full_name": "New Artist",
        "phone": "+353 1 111 1111",
        "role": role,
        "acts_as_artist": False,
        "artist_name": "Needle",
    }


def test_owner_creates_an_account_that_is_active_right_away(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 2.6: conta criada por gestor ja nasce ativa."""
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(f"{api_prefix}/users", json=_new_account_payload(), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ACTIVE"
    assert "password" not in body and "password_hash" not in body


def test_manager_cannot_create_a_manager(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 2.2: o gerente nao promove ninguem a perfil administrativo."""
    AccountBuilder(session).create(
        email="manager@studio.ie", password=PASSWORD, role=UserRole.MANAGER
    )
    session.commit()
    headers = _sign_in(client, api_prefix, "manager@studio.ie")

    response = client.post(
        f"{api_prefix}/users", json=_new_account_payload(role="MANAGER"), headers=headers
    )

    assert response.status_code == 403


def test_resident_cannot_create_accounts(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(
        email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT
    )
    session.commit()
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = client.post(f"{api_prefix}/users", json=_new_account_payload(), headers=headers)

    assert response.status_code == 403


def test_resident_cannot_list_accounts(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 2.3: artista nao acessa dados de outros artistas."""
    AccountBuilder(session).create(
        email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT
    )
    session.commit()
    _sign_in(client, api_prefix, "artist@studio.ie")

    assert client.get(f"{api_prefix}/users").status_code == 403


def test_duplicate_email_is_refused(client: TestClient, session: Session, api_prefix: str) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    first = client.post(f"{api_prefix}/users", json=_new_account_payload(), headers=headers)
    second = client.post(f"{api_prefix}/users", json=_new_account_payload(), headers=headers)

    assert first.status_code == 201
    assert second.status_code == 422


def test_creating_an_account_without_csrf_header_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(f"{api_prefix}/users", json=_new_account_payload())

    assert response.status_code == 403


def test_blocking_an_account_revokes_its_sessions_and_is_audited(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    builder = AccountBuilder(session)
    builder.create(email="owner@studio.ie", password=PASSWORD)
    target = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    session.commit()

    # O artista entra e passa a ter sessao viva.
    artist = TestClient(client.app)
    artist.post(
        f"{api_prefix}/auth/login", json={"email": "artist@studio.ie", "password": PASSWORD}
    )
    assert artist.get(f"{api_prefix}/auth/me").status_code == 200

    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    response = client.post(
        f"{api_prefix}/users/{target.id}/block",
        json={"reason": "Left the studio"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["revoked_sessions"] == 1
    assert artist.get(f"{api_prefix}/auth/me").status_code == 401

    audited = session.execute(
        text("SELECT reason FROM audit_log WHERE action = 'ACCOUNT_BLOCKED'")
    ).scalar_one()
    assert audited == "Left the studio"


def test_manager_cannot_block_an_owner(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    builder = AccountBuilder(session)
    builder.create(email="manager@studio.ie", password=PASSWORD, role=UserRole.MANAGER)
    owner = builder.create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "manager@studio.ie")

    response = client.post(
        f"{api_prefix}/users/{owner.id}/block", json={"reason": "no"}, headers=headers
    )

    assert response.status_code == 403
    session.expire_all()
    assert session.get(UserAccount, owner.id).status == UserStatus.ACTIVE


def test_last_active_owner_cannot_be_blocked(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 2.5: o estudio nunca pode ficar sem administracao."""
    owner = AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/users/{owner.id}/block", json={"reason": "stepping down"}, headers=headers
    )

    assert response.status_code == 422
    assert "last active owner" in response.json()["detail"].lower()


def test_an_owner_can_be_blocked_when_another_remains_active(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    builder = AccountBuilder(session)
    builder.create(email="owner@studio.ie", password=PASSWORD)
    second = builder.create(email="owner2@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/users/{second.id}/block", json={"reason": "on leave"}, headers=headers
    )

    assert response.status_code == 200


def test_unblocking_restores_access(client: TestClient, session: Session, api_prefix: str) -> None:
    builder = AccountBuilder(session)
    builder.create(email="owner@studio.ie", password=PASSWORD)
    target = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    client.post(
        f"{api_prefix}/users/{target.id}/block", json={"reason": "temporary"}, headers=headers
    )
    response = client.post(f"{api_prefix}/users/{target.id}/unblock", headers=headers)

    assert response.status_code == 200
    session.expire_all()
    assert session.get(UserAccount, target.id).status == UserStatus.ACTIVE


def test_listing_accounts_is_available_to_staff(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    builder = AccountBuilder(session)
    builder.create(email="owner@studio.ie", password=PASSWORD)
    builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    session.commit()
    _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.get(f"{api_prefix}/users")

    assert response.status_code == 200
    emails = {account["email"] for account in response.json()}
    assert emails == {"owner@studio.ie", "artist@studio.ie"}


def test_created_account_can_sign_in(client: TestClient, session: Session, api_prefix: str) -> None:
    """Fecha o ciclo: a conta criada pelo gestor funciona de verdade."""
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    client.post(f"{api_prefix}/users", json=_new_account_payload(), headers=headers)

    fresh = TestClient(client.app)
    response = fresh.post(
        f"{api_prefix}/auth/login",
        json={"email": "new@studio.ie", "password": "a-long-enough-password"},
    )

    assert response.status_code == 200
    stored = session.execute(
        select(UserAccount).where(UserAccount.email == "new@studio.ie")
    ).scalar_one()
    assert stored.created_by is not None
