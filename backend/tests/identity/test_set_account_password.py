"""Senha definida pela area de gerenciamento (RN 2.7).

Duas garantias importam aqui, e nenhuma das duas e sobre trocar a senha.

A primeira: **a senha antiga para de valer e as sessoes caem**. Uma senha
trocada sem encerrar sessao deixaria em pe exatamente o acesso que a troca
queria cortar -- quem estivesse logado continuaria dentro.

A segunda: **a senha nao aparece em lugar nenhum**. A regra proibe que gerentes
e proprietarios visualizem senhas; definir uma nova nao e ver a antiga, e nem a
nova pode sobrar na auditoria.
"""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.identity.domain.user_role import UserRole
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "a brand new passphrase"


def _sign_in(client: TestClient, api_prefix: str, email: str, password: str = PASSWORD):
    return client.post(f"{api_prefix}/auth/login", json={"email": email, "password": password})


def _headers(client: TestClient) -> dict[str, str]:
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _setup(session: Session) -> dict[str, uuid.UUID]:
    builder = AccountBuilder(session)
    owner = builder.create(email="owner@studio.ie", password=PASSWORD)
    manager = builder.create(
        email="manager@studio.ie", password=PASSWORD, role=UserRole.MANAGER
    )
    artist = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    session.commit()
    return {"owner": owner.id, "manager": manager.id, "artist": artist.id}


def _set_password(
    client: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    account_id: uuid.UUID,
    password: str = NEW_PASSWORD,
):
    return client.put(
        f"{api_prefix}/users/{account_id}/password",
        json={"password": password},
        headers=headers,
    )


def test_management_gives_an_artist_a_new_password(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    assert _sign_in(client, api_prefix, "owner@studio.ie").status_code == 200

    response = _set_password(client, api_prefix, _headers(client), ids["artist"])

    assert response.status_code == 200, response.text


def test_the_new_password_works_and_the_old_one_stops(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O que o gestor espera ao redefinir: a pessoa entra com a senha nova e
    nao entra mais com a antiga."""
    ids = _setup(session)
    _sign_in(client, api_prefix, "owner@studio.ie")
    _set_password(client, api_prefix, _headers(client), ids["artist"])
    client.post(f"{api_prefix}/auth/logout", headers=_headers(client))

    assert _sign_in(client, api_prefix, "artist@studio.ie", NEW_PASSWORD).status_code == 200
    client.post(f"{api_prefix}/auth/logout", headers=_headers(client))
    assert _sign_in(client, api_prefix, "artist@studio.ie", PASSWORD).status_code == 401


def test_a_password_shorter_than_the_minimum_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    _sign_in(client, api_prefix, "owner@studio.ie")

    response = _set_password(client, api_prefix, _headers(client), ids["artist"], "short")

    assert response.status_code == 422


def test_the_manager_resets_an_artist(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A RN 2.6 da ao gerente a administracao de residentes e guests."""
    ids = _setup(session)
    _sign_in(client, api_prefix, "manager@studio.ie")

    response = _set_password(client, api_prefix, _headers(client), ids["artist"])

    assert response.status_code == 200, response.text


def test_the_manager_cannot_reset_an_owner(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Deixar passar seria entregar a conta do proprietario ao gerente: ele
    define a senha e entra como ele."""
    ids = _setup(session)
    _sign_in(client, api_prefix, "manager@studio.ie")

    response = _set_password(client, api_prefix, _headers(client), ids["owner"])

    assert response.status_code == 403


def test_an_artist_cannot_reset_anyone(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    _sign_in(client, api_prefix, "artist@studio.ie")

    response = _set_password(client, api_prefix, _headers(client), ids["artist"])

    assert response.status_code == 403


def test_the_password_never_reaches_the_audit_trail(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O teste que mais importa deste arquivo. A RN 2.7 diz que senhas nunca
    poderao ser visualizadas por gerentes ou proprietarios -- e a auditoria e
    lida por eles."""
    ids = _setup(session)
    _sign_in(client, api_prefix, "owner@studio.ie")
    _set_password(client, api_prefix, _headers(client), ids["artist"])

    trail = session.execute(
        text(
            "SELECT old_values, new_values FROM audit_log"
            " WHERE action = 'ACCOUNT_PASSWORD_SET' AND entity_id = :id"
        ),
        {"id": str(ids["artist"])},
    ).one()

    assert NEW_PASSWORD not in str(trail)
    assert "password" not in str(trail[1]).lower()


def test_the_account_is_signed_out_everywhere(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Uma senha trocada sem encerrar sessao deixaria em pe o acesso que a troca
    queria cortar."""
    ids = _setup(session)
    _sign_in(client, api_prefix, "owner@studio.ie")
    _set_password(client, api_prefix, _headers(client), ids["artist"])

    live = session.execute(
        text("SELECT count(*) FROM user_session WHERE user_id = :id AND revoked_at IS NULL"),
        {"id": str(ids["artist"])},
    ).scalar_one()

    assert live == 0
