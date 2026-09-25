from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.models.user_session import UserSession
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"
EMAIL = "owner@studio.ie"


def _sign_in(client: TestClient, api_prefix: str) -> None:
    """Falha aqui, e nao duas linhas adiante, se a pre-condicao nao se cumprir."""
    response = client.post(
        f"{api_prefix}/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"


def test_authenticated_user_is_returned(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email=EMAIL, password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix)

    response = client.get(f"{api_prefix}/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == EMAIL
    assert body["role"] == "OWNER"
    assert "password_hash" not in body


def test_request_without_session_is_refused(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/auth/me")

    assert response.status_code == 401


def test_logout_revokes_the_session(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email=EMAIL, password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix)
    settings = Settings()

    logout = client.post(
        f"{api_prefix}/auth/logout",
        headers={settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)},
    )

    assert logout.status_code == 200
    assert client.get(f"{api_prefix}/auth/me").status_code == 401


def test_blocking_the_account_revokes_access_immediately(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 2.5: bloquear encerra o acesso na hora, mesmo com sessao no prazo."""
    account = AccountBuilder(session).create(email=EMAIL, password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix)
    assert client.get(f"{api_prefix}/auth/me").status_code == 200

    session.execute(
        update(UserAccount).where(UserAccount.id == account.id).values(status=UserStatus.BLOCKED)
    )
    session.commit()

    assert client.get(f"{api_prefix}/auth/me").status_code == 401


def test_session_expires_after_idle_window(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email=EMAIL, password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix)

    session.execute(
        update(UserSession).values(idle_expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    session.commit()

    assert client.get(f"{api_prefix}/auth/me").status_code == 401


def test_session_expires_at_the_absolute_limit(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Mesmo em uso continuo, a sessao morre em 12 horas."""
    AccountBuilder(session).create(email=EMAIL, password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix)

    session.execute(
        update(UserSession).values(absolute_expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    session.commit()

    assert client.get(f"{api_prefix}/auth/me").status_code == 401
