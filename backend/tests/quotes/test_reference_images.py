"""Imagens de referência do orçamento (RN-ORC-004).

O ponto que estes testes protegem não é o upload em si, é o acesso. A imagem é
dado pessoal — a tatuagem que alguém quer, ligada ao nome dessa pessoa no
cadastro — e o desenho escolhido não gera nenhum endereço que a devolva sem a
sessão. O cenário negativo que mais importa é o artista de fora conseguindo ler a
imagem de um orçamento que não é dele.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"
PNG = b"\x89PNG\r\n\x1a\n-bytes-de-referencia"


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _setup(session: Session) -> dict[str, str]:
    builder = AccountBuilder(session)
    owner = builder.create(email="owner@studio.ie", password=PASSWORD)
    artist = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    other = builder.create(email="other@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    session.add(subject)
    session.flush()
    session.commit()
    return {
        "owner": str(owner.id),
        "artist": str(artist.id),
        "other": str(other.id),
        "client": str(subject.id),
    }


def _quote_payload(client_id: str) -> dict[str, object]:
    return {
        "client_id": client_id,
        "origin": "ARTIST_OWN",
        "description": "Blackwork forearm sleeve",
        "body_region": "Left forearm",
        "size_estimate": "20cm",
        "total_value": "1000.00",
        "planned_sessions": 4,
        "planned_value_per_session": "250.00",
        "estimated_duration_minutes": 180,
    }


def _create_quote(
    caller: TestClient, api_prefix: str, headers: dict[str, str], client_id: str
) -> str:
    response = caller.post(f"{api_prefix}/quotes", json=_quote_payload(client_id), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _attach(
    caller: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    quote_id: str,
    content: bytes = PNG,
    content_type: str = "image/png",
    filename: str = "reference.png",
):
    return caller.post(
        f"{api_prefix}/quotes/{quote_id}/reference-images",
        files={"file": (filename, content, content_type)},
        headers=headers,
    )


def test_artist_attaches_a_reference_image_to_own_pending_quote(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])

    response = _attach(client, api_prefix, headers, quote_id)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["content_type"] == "image/png"
    assert body["byte_size"] == len(PNG)
    assert body["content_path"].endswith(f"/reference-images/{body['id']}/content")
    assert "object_key" not in body


def test_the_content_endpoint_returns_the_stored_bytes(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O caminho completo: gravar no volume e ler de volta pela rota autenticada."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])
    attached = _attach(client, api_prefix, headers, quote_id).json()

    response = client.get(attached["content_path"])

    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "private, no-store"


def test_the_content_endpoint_refuses_a_visitor_without_session(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A garantia central do desenho: sem cookie, nenhuma imagem sai."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])
    attached = _attach(client, api_prefix, headers, quote_id).json()

    anonymous = TestClient(client.app)
    response = anonymous.get(attached["content_path"])

    assert response.status_code == 401


def test_another_artist_cannot_read_or_attach(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A imagem segue a visibilidade do orçamento, não a sua própria."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])
    attached = _attach(client, api_prefix, headers, quote_id).json()

    intruder = TestClient(client.app)
    intruder_headers = _sign_in(intruder, api_prefix, "other@studio.ie")

    listing = intruder.get(f"{api_prefix}/quotes/{quote_id}/reference-images")
    reading = intruder.get(attached["content_path"])
    attaching = _attach(intruder, api_prefix, intruder_headers, quote_id)

    assert listing.status_code == 403
    assert reading.status_code == 403
    assert attaching.status_code == 403


def test_an_image_of_another_quote_is_not_served_through_this_quote(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Sem esta conferência, o controle ficaria no orçamento da URL e o dado viria
    de outro: bastaria pedir a imagem alheia por um orçamento próprio."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    first = _create_quote(client, api_prefix, owner_headers, ids["client"])
    second = _create_quote(client, api_prefix, owner_headers, ids["client"])
    attached = _attach(client, api_prefix, owner_headers, first).json()

    response = client.get(
        f"{api_prefix}/quotes/{second}/reference-images/{attached['id']}/content"
    )

    assert response.status_code == 422


def test_unsupported_image_type_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])

    response = _attach(
        client,
        api_prefix,
        headers,
        quote_id,
        content=b"%PDF-1.4",
        content_type="application/pdf",
        filename="reference.pdf",
    )

    assert response.status_code == 422
    assert "image/png" in response.json()["detail"]


def test_an_image_above_the_size_limit_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O limite confirmado é 10 MB; um byte acima já não entra."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])
    oversized = b"\0" * (Settings().reference_image_max_bytes + 1)

    response = _attach(client, api_prefix, headers, quote_id, content=oversized)

    assert response.status_code == 422
    assert "10 MB" in response.json()["detail"]


def test_an_empty_file_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])

    response = _attach(client, api_prefix, headers, quote_id, content=b"")

    assert response.status_code == 422


def test_the_quote_takes_no_more_than_the_configured_number_of_images(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])
    limit = Settings().reference_image_max_per_quote

    for _ in range(limit):
        assert _attach(client, api_prefix, headers, quote_id).status_code == 201

    refused = _attach(client, api_prefix, headers, quote_id)

    assert refused.status_code == 422
    assert str(limit) in refused.json()["detail"]
    assert len(client.get(f"{api_prefix}/quotes/{quote_id}/reference-images").json()) == limit


def test_attaching_does_not_send_an_approved_quote_back_to_pending(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Imagem de referência não é termo do acordo (RN-ORC-003).

    Reabrir a aprovação porque alguém acrescentou uma foto puniria o cuidado de
    documentar melhor o trabalho."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    quote_id = _create_quote(client, api_prefix, owner_headers, ids["client"])
    client.post(f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=owner_headers)

    attaching = _attach(client, api_prefix, owner_headers, quote_id)
    quote = client.get(f"{api_prefix}/quotes/{quote_id}").json()

    assert attaching.status_code == 201
    assert quote["status"] == "APPROVED"
    assert quote["artist_percentage"] == "70.00"


def test_resident_cannot_attach_to_an_approved_quote_but_management_can(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A permissão de anexar é a de editar: no aprovado, só o gestor."""
    ids = _setup(session)
    artist_headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, artist_headers, ids["client"])

    owner = TestClient(client.app)
    owner_headers = _sign_in(owner, api_prefix, "owner@studio.ie")
    owner.post(f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=owner_headers)

    by_artist = _attach(client, api_prefix, artist_headers, quote_id)
    by_owner = _attach(owner, api_prefix, owner_headers, quote_id)

    assert by_artist.status_code == 403
    assert by_owner.status_code == 201


def test_removing_an_image_deletes_the_file_as_well(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O arquivo é apagado de verdade, não só desvinculado: imagem é dado
    pessoal, e guardar o que ninguém mais usa contraria a RN-CLI-007."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, ids["client"])
    attached = _attach(client, api_prefix, headers, quote_id).json()

    removal = client.delete(
        f"{api_prefix}/quotes/{quote_id}/reference-images/{attached['id']}", headers=headers
    )

    assert removal.status_code == 204
    assert client.get(f"{api_prefix}/quotes/{quote_id}/reference-images").json() == []
    assert client.get(attached["content_path"]).status_code == 422
