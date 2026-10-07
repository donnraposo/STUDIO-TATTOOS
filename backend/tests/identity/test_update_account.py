"""Edicao de cadastro pela area de gerenciamento (RN 2.1, 2.2 e 2.6).

A regra autoriza desde sempre -- "gerente ou proprietario pode autorizar,
**editar** ou bloquear cadastros de residentes e guests" --, e ate 07/10/2026 so
existiam criar e bloquear: corrigir um telefone exigia o banco.

O que mais importa aqui e o perfil. A RN 2.6 diz que "o gerente nao pode
promover usuarios nem alterar perfis de acesso", e deixar passar pela edicao
abriria pela porta de tras o caminho que a RN 2.2 fecha na criacao: o gerente
cria um par e pede que o par o promova.
"""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.identity.domain.user_role import UserRole
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
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


def _edit(
    client: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    account_id: uuid.UUID,
    **overrides: object,
):
    body = {
        "email": "artist@studio.ie",
        "full_name": "Artist",
        "phone": "+353 87 111 1111",
        "role": "RESIDENT",
        "acts_as_artist": False,
        "artist_name": "Artist",
    }
    body.update(overrides)
    return client.put(f"{api_prefix}/users/{account_id}", json=body, headers=headers)


def test_management_corrects_a_cadastro(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _edit(
        client,
        api_prefix,
        headers,
        ids["artist"],
        full_name="Ytalo Lyra",
        phone="+353 86 222 2222",
        artist_name="Ytalo",
    )

    assert response.status_code == 200, response.text
    assert response.json()["full_name"] == "Ytalo Lyra"
    assert response.json()["phone"] == "+353 86 222 2222"
    assert response.json()["artist_name"] == "Ytalo"


def test_the_owner_changes_a_role(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 2.1: o proprietario atribui e permuta perfis."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _edit(client, api_prefix, headers, ids["artist"], role="GUEST")

    assert response.status_code == 200, response.text
    assert response.json()["role"] == "GUEST"


def test_the_manager_cannot_change_a_role(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O teste que mais importa deste arquivo. Sem ele, a edicao abriria o
    caminho que a criacao fecha: o gerente cria um par e pede a promocao."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "manager@studio.ie")

    response = _edit(client, api_prefix, headers, ids["artist"], role="MANAGER")

    assert response.status_code == 403


def test_the_manager_cannot_swap_resident_for_guest_either(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A RN 2.6 nao fala so em promocao: diz "nem alterar perfis de acesso".
    Trocar residente por guest muda a exigencia de sinal (RN-GST-004) e o
    repasse de quem o estudio indica -- e o gerente pode criar os dois perfis,
    entao a politica de criacao sozinha deixaria isso passar."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "manager@studio.ie")

    response = _edit(client, api_prefix, headers, ids["artist"], role="GUEST")

    assert response.status_code == 403


def test_the_manager_still_corrects_the_rest(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A RN 2.6 da a edicao ao gerente; o que ela tira dele e o perfil. Recusar
    tudo o impediria de corrigir um telefone."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "manager@studio.ie")

    response = _edit(client, api_prefix, headers, ids["artist"], full_name="Lisa")

    assert response.status_code == 200, response.text
    assert response.json()["full_name"] == "Lisa"


def test_the_manager_cannot_edit_management(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 2.2 e 2.5: o gerente administra residentes e guests."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "manager@studio.ie")

    response = _edit(
        client,
        api_prefix,
        headers,
        ids["owner"],
        email="owner@studio.ie",
        full_name="Someone Else",
        role="OWNER",
        acts_as_artist=True,
        artist_name="Nyx",
    )

    assert response.status_code == 403


def test_the_last_active_owner_cannot_lose_the_role(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A mesma garantia da RN 2.5 pela outra porta: bloquear e rebaixar esvaziam
    a administracao do mesmo jeito, e rebaixar nao tem volta -- ninguem sobraria
    para criar outro proprietario."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _edit(
        client,
        api_prefix,
        headers,
        ids["owner"],
        email="owner@studio.ie",
        full_name="Aoife Byrne",
        role="MANAGER",
        artist_name=None,
    )

    assert response.status_code == 422


def test_an_artist_cannot_be_left_without_an_artist_name(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O banco recusa em `ck_user_account_artist_name_required`; aqui a recusa
    diz o que fazer em vez de devolver erro de integridade."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _edit(client, api_prefix, headers, ids["artist"], artist_name=None)

    assert response.status_code == 422


def test_an_email_already_in_use_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _edit(client, api_prefix, headers, ids["artist"], email="manager@studio.ie")

    assert response.status_code == 422


def test_keeping_the_same_email_is_not_a_duplicate(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Quem corrige so o telefone manda o cadastro inteiro de volta, com o
    proprio e-mail. Compara-lo com ele mesmo recusaria toda edicao."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _edit(client, api_prefix, headers, ids["artist"], phone="+353 1 234 5678")

    assert response.status_code == 200, response.text


def test_the_artist_cannot_edit_anyone(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = _edit(client, api_prefix, headers, ids["artist"], full_name="Myself")

    assert response.status_code == 403


def test_the_edit_is_recorded_with_what_changed(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 2.6: "autorizacao, rejeicao, edicao, bloqueio e alteracao de perfil
    devem ficar registrados no historico"."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    _edit(client, api_prefix, headers, ids["artist"], full_name="Lisa")

    trail = session.execute(
        text(
            "SELECT old_values, new_values FROM audit_log"
            " WHERE action = 'ACCOUNT_UPDATED' AND entity_id = :id"
            " ORDER BY created_at DESC LIMIT 1"
        ),
        {"id": str(ids["artist"])},
    ).one()

    assert trail[0]["full_name"] != "Lisa"
    assert trail[1]["full_name"] == "Lisa"
