"""Quem trouxe o cliente ao estudio (RN-CLI-002, RN-CLI-003 e RN-GST-005).

A regra decide dinheiro a partir de uma pergunta que o sistema nao sabia
responder: "o cliente retornou ao mesmo artista **que o trouxe**?". O campo
antigo respondia outra coisa -- quem digitou o cadastro --, e as duas divergem
justamente no caso que importa: a RN-GST-005 manda o gestor cadastrar o cliente
indicado pelo estudio, e ali quem cadastrou nao trouxe ninguem.

O que mais importa aqui e a contradicao: `STUDIO` com um artista junto nao pode
existir. Gravada, ela nao aparece em tela nenhuma e decide repasse depois.
"""

from fastapi.testclient import TestClient
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


def _setup(session: Session) -> dict[str, str]:
    builder = AccountBuilder(session)
    owner = builder.create(email="owner@studio.ie", password=PASSWORD)
    artist = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    guest = builder.create(email="guest@studio.ie", password=PASSWORD, role=UserRole.GUEST)
    session.commit()
    return {"owner": str(owner.id), "artist": str(artist.id), "guest": str(guest.id)}


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "Aoife", "phone": "+353 87 111 1111"}
    payload.update(overrides)
    return payload


def test_the_artist_who_registers_is_the_one_who_brought(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O caso corrente: o residente cadastra o proprio cliente. Obriga-lo a
    escolher-se numa lista seria ruido."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = client.post(f"{api_prefix}/clients", json=_payload(), headers=headers)

    assert response.status_code == 201, response.text
    assert response.json()["client"]["brought_by_artist_id"] == ids["artist"]


def test_a_studio_referral_has_no_artist(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-002: o cliente chegou ao salao, nao pela mao de alguem. A ausencia
    e o dado, e nao a falta dele."""
    _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/clients", json=_payload(source="STUDIO"), headers=headers
    )

    assert response.status_code == 201, response.text
    assert response.json()["client"]["brought_by_artist_id"] is None


def test_a_studio_referral_with_an_artist_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A contradicao nao pode ser gravada: ninguem a ve no banco e ela decide
    repasse depois."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/clients",
        json=_payload(source="STUDIO", brought_by_artist_id=ids["artist"]),
        headers=headers,
    )

    assert response.status_code == 422


def test_management_records_the_client_a_guest_brought(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-GST-005: o gestor cadastra e associa ao guest. Quem cadastrou e o
    gestor; quem trouxe e outra pessoa, e sao campos diferentes."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/clients",
        json=_payload(brought_by_artist_id=ids["guest"]),
        headers=headers,
    )

    assert response.status_code == 201, response.text
    body = response.json()["client"]
    assert body["brought_by_artist_id"] == ids["guest"]
    assert body["registered_by_artist_id"] == ids["owner"]


def test_an_artist_cannot_name_a_colleague_as_who_brought(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Apontar um colega como quem trouxe mexeria no repasse alheio."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = client.post(
        f"{api_prefix}/clients",
        json=_payload(brought_by_artist_id=ids["guest"]),
        headers=headers,
    )

    assert response.status_code == 403


def test_editing_the_contact_does_not_touch_who_brought(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O artista corrige o proprio cliente sem esbarrar na alcada da origem.

    Sem contratos separados para criar e editar, o padrao do campo faria toda
    correcao de telefone tentar reescrever a origem -- e o artista levaria 403
    sem entender por que."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    created = client.post(f"{api_prefix}/clients", json=_payload(), headers=headers).json()

    response = client.put(
        f"{api_prefix}/clients/{created['client']['id']}",
        json=_payload(phone="+353 87 999 9999"),
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["phone"] == "+353 87 999 9999"
    assert response.json()["brought_by_artist_id"] == ids["artist"]


def test_only_management_changes_who_brought(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-003: alterar a origem e de gerente e proprietario."""
    _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    created = client.post(f"{api_prefix}/clients", json=_payload(), headers=headers).json()

    response = client.put(
        f"{api_prefix}/clients/{created['client']['id']}",
        json=_payload(source="STUDIO"),
        headers=headers,
    )

    assert response.status_code == 403


def test_management_corrects_who_brought(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    _setup(session)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    created = client.post(f"{api_prefix}/clients", json=_payload(), headers=artist).json()

    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    response = client.put(
        f"{api_prefix}/clients/{created['client']['id']}",
        json=_payload(source="STUDIO"),
        headers=owner,
    )

    assert response.status_code == 200, response.text
    assert response.json()["brought_by_artist_id"] is None


def test_an_existing_client_keeps_an_unknown_source(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Os cadastros anteriores a migracao `0008` ficam nulos, e isso e correto.

    O sistema nao sabe quem os trouxe. Gravar quem cadastrou como se fosse quem
    trouxe seria inventar uma afirmacao que ninguem fez -- e ela sairia do banco
    como verdade no primeiro repasse."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    created = client.post(
        f"{api_prefix}/clients", json=_payload(source="STUDIO"), headers=headers
    ).json()

    found = client.get(f"{api_prefix}/clients/{created['client']['id']}")

    assert found.json()["brought_by_artist_id"] is None
    assert found.json()["registered_by_artist_id"] == ids["owner"]
