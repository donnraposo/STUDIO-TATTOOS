from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"
EMAIL = "owner@studio.ie"


def _sign_in(client: TestClient, api_prefix: str) -> None:
    """Falha aqui, e nao duas linhas adiante, se a pre-condicao nao se cumprir."""
    response = client.post(
        f"{api_prefix}/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"


def test_mutating_request_without_csrf_header_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O cookie de sessao viaja sozinho em requisicao disparada por outro site;
    o cabecalho CSRF e o que um terceiro nao consegue montar."""
    AccountBuilder(session).create(email=EMAIL, password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix)

    response = client.post(f"{api_prefix}/auth/logout")

    assert response.status_code == 403
    assert client.get(f"{api_prefix}/auth/me").status_code == 200


def test_mutating_request_with_mismatched_csrf_token_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email=EMAIL, password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix)
    settings = Settings()

    response = client.post(
        f"{api_prefix}/auth/logout",
        headers={settings.csrf_header_name: "forged-token"},
    )

    assert response.status_code == 403


def test_mutating_request_with_matching_csrf_token_is_accepted(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    AccountBuilder(session).create(email=EMAIL, password=PASSWORD)
    session.commit()
    _sign_in(client, api_prefix)
    settings = Settings()

    response = client.post(
        f"{api_prefix}/auth/logout",
        headers={settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)},
    )

    assert response.status_code == 200
