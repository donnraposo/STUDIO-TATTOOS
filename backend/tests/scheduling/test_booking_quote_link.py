"""O agendamento aponta para o orcamento que nasceu com ele (migracao 0011).

Desde 07/10/2026 o tatuador escolhe a maca e preenche os dados da tatuagem no
mesmo formulario: o orcamento nasce **junto** do agendamento. Sem um elo entre
os dois antes de qualquer aprovacao, o gestor que abre o horario nao teria como
aprovar o orcamento dali -- e a RN-ORC-002 exige que alguem o aprove.

Nulo e caso legitimo e nao falta de dado: o guest nao acessa o modulo de
orcamentos (RN-ORC-001) e continua agendando para clientes proprios sem nenhum.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from app.modules.scheduling.infrastructure.models.bench import Bench
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
    artist = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    guest = builder.create(email="guest@studio.ie", password=PASSWORD, role=UserRole.GUEST)
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    bench = Bench(number=1)
    session.add_all([subject, bench])
    session.flush()
    session.commit()
    return {
        "owner": owner.id,
        "artist": artist.id,
        "guest": guest.id,
        "client": subject.id,
        "bench": bench.id,
    }


def _quote(client: TestClient, api_prefix: str, headers: dict[str, str], ids) -> str:
    created = client.post(
        f"{api_prefix}/quotes",
        json={
            "client_id": str(ids["client"]),
            "artist_id": str(ids["artist"]),
            "origin": "ARTIST_OWN",
            "description": "Session 1 of 3 - Blackwork sleeve",
            "body_region": "Left forearm",
            "size_estimate": "20cm",
            "total_value": "250.00",
            "planned_sessions": 1,
            "planned_value_per_session": "250.00",
            "estimated_duration_minutes": 120,
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


def _book(
    client: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    ids,
    quote_id: str | None,
    hour: int = 11,
    artist_id: uuid.UUID | None = None,
    deposit: str | None = None,
):
    start = (datetime.now(UTC) + timedelta(days=1)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    body = {
        "client_id": str(ids["client"]),
        "bench_id": str(ids["bench"]),
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=2)).isoformat(),
    }
    # O guest agenda para si mesmo e omite o artista; mandar o identificador de
    # outra pessoa e exatamente o que a politica recusa.
    if artist_id is not None:
        body["artist_id"] = str(artist_id)
    if quote_id is not None:
        body["quote_id"] = quote_id
    if deposit is not None:
        body["deposit_amount"] = deposit
    return client.post(f"{api_prefix}/bookings", json=body, headers=headers)


def test_the_booking_carries_the_work_it_serves(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _quote(client, api_prefix, headers, ids)

    response = _book(client, api_prefix, headers, ids, quote_id, artist_id=ids["artist"])

    assert response.status_code == 201, response.text
    assert response.json()["quote_id"] == quote_id


def test_the_link_survives_the_listing(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A agenda e onde o gestor abre o horario para decidir; se o elo nao
    viesse na listagem, ele teria de buscar o orcamento por outro caminho."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _quote(client, api_prefix, headers, ids)
    _book(client, api_prefix, headers, ids, quote_id, artist_id=ids["artist"])

    listed = client.get(f"{api_prefix}/bookings", headers=headers).json()

    assert any(booking["quote_id"] == quote_id for booking in listed)


def test_a_booking_without_a_quote_is_still_valid(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-001: o guest nao acessa orcamentos e agenda para clientes
    proprios. Exigir o elo o tiraria da agenda."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "guest@studio.ie")

    response = _book(client, api_prefix, headers, ids, None, hour=15)

    assert response.status_code == 201, response.text
    assert response.json()["quote_id"] is None


def test_the_quote_cannot_be_deleted_while_a_booking_points_at_it(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Nao ha rota de exclusao de orcamento, e o banco recusaria de qualquer
    forma: um horario apontando para um trabalho que sumiu nao diz mais o que
    sera tatuado ali."""
    from sqlalchemy.exc import IntegrityError

    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _quote(client, api_prefix, headers, ids)
    _book(client, api_prefix, headers, ids, quote_id, artist_id=ids["artist"])

    from sqlalchemy import text

    try:
        session.execute(text("DELETE FROM quote WHERE id = :id"), {"id": quote_id})
        session.flush()
        recusou = False
    except IntegrityError:
        session.rollback()
        recusou = True

    assert recusou, "o banco deveria recusar apagar um orcamento com horario marcado"


def test_the_booking_carries_the_deposit_the_artist_agreed(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Migracao 0012. Cada artista cobra o seu sinal, e quem sabe quanto foi e
    quem recebeu -- por isso o valor e dito ao marcar o horario."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = _book(
        client, api_prefix, headers, ids, None, hour=16, artist_id=ids["artist"],
        deposit="80.00",
    )

    assert response.status_code == 201, response.text
    assert response.json()["deposit_amount"] == "80.00"


def test_a_booking_without_a_stated_deposit_falls_back_to_the_studio_default(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Nulo significa "use o padrao do estudio". Quem nao disse nada nao esta
    dizendo "sem sinal" -- e e o caso de todo agendamento criado antes de
    08/10/2026."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = _book(
        client, api_prefix, headers, ids, None, hour=17, artist_id=ids["artist"]
    )

    assert response.status_code == 201, response.text
    assert response.json()["deposit_amount"] is None


def test_a_deposit_of_zero_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Sinal zero e "sem sinal", e isso se diz deixando o campo vazio -- nao
    escrevendo zero nele. O banco recusa pelo mesmo motivo."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = _book(
        client, api_prefix, headers, ids, None, hour=18, artist_id=ids["artist"],
        deposit="0",
    )

    assert response.status_code == 422
