from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.identity.domain.user_status import UserStatus
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"


def test_login_with_valid_credentials_opens_a_session(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()

    response = client.post(
        f"{api_prefix}/auth/login", json={"email": "owner@studio.ie", "password": PASSWORD}
    )

    assert response.status_code == 200
    settings = Settings()
    assert settings.session_cookie_name in response.cookies
    assert settings.csrf_cookie_name in response.cookies


def test_session_cookie_is_http_only(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O cookie de sessao nao pode ser legivel por script, sob pena de XSS
    conseguir roubar a sessao."""
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()

    response = client.post(
        f"{api_prefix}/auth/login", json={"email": "owner@studio.ie", "password": PASSWORD}
    )

    session_cookie = next(
        value for value in response.headers.get_list("set-cookie") if "studio_session" in value
    )
    assert "HttpOnly" in session_cookie

    csrf_cookie = next(
        value for value in response.headers.get_list("set-cookie") if "studio_csrf" in value
    )
    assert "HttpOnly" not in csrf_cookie


def test_login_with_wrong_password_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()

    response = client.post(
        f"{api_prefix}/auth/login", json={"email": "owner@studio.ie", "password": "wrong"}
    )

    assert response.status_code == 401


def test_unknown_email_and_wrong_password_are_indistinguishable(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Login nao pode revelar se um e-mail existe."""
    AccountBuilder(session).create(email="owner@studio.ie", password=PASSWORD)
    session.commit()

    wrong_password = client.post(
        f"{api_prefix}/auth/login", json={"email": "owner@studio.ie", "password": "wrong"}
    )
    unknown_email = client.post(
        f"{api_prefix}/auth/login", json={"email": "ghost@studio.ie", "password": "wrong"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_blocked_account_cannot_authenticate(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(
        email="blocked@studio.ie", password=PASSWORD, status=UserStatus.BLOCKED
    )
    session.commit()

    response = client.post(
        f"{api_prefix}/auth/login", json={"email": "blocked@studio.ie", "password": PASSWORD}
    )

    assert response.status_code == 401


def test_pending_account_cannot_authenticate(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Cadastro pendente de autorizacao nao concede acesso (RN 2.6)."""
    AccountBuilder(session).create(
        email="pending@studio.ie", password=PASSWORD, status=UserStatus.PENDING_APPROVAL
    )
    session.commit()

    response = client.post(
        f"{api_prefix}/auth/login", json={"email": "pending@studio.ie", "password": PASSWORD}
    )

    assert response.status_code == 401
