"""O corpo do 409 precisa levar a reserva existente.

A RN-AGE-007 exige um modal que **mostre o agendamento conflitante** e nao
permita ignorar o conflito. Uma resposta com apenas a mensagem de erro nao
sustenta esse modal: a tela teria como dizer "ocupado", mas nao como mostrar por
quem nem abrir o agendamento.

O defeito que este arquivo protege e silencioso: tudo funciona, o conflito e
recusado corretamente pelo banco, e so a tela fica sem poder cumprir a regra.
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"
START = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _setup(session: Session) -> dict[str, str]:
    builder = AccountBuilder(session)
    owner = builder.create(email="owner@studio.ie", password=PASSWORD)
    artist = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=owner.id)
    session.add(subject)
    session.flush()
    session.commit()
    return {"artist": str(artist.id), "client": str(subject.id)}


def _book(
    client: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    ids: dict[str, str],
    booth_id: str,
    hours_offset: int,
    artist_id: str | None = None,
):
    start = START + timedelta(hours=hours_offset)
    payload = {
        "client_id": ids["client"],
        "booth_id": booth_id,
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=2)).isoformat(),
        "approve_immediately": True,
    }
    if artist_id:
        payload["artist_id"] = artist_id
    return client.post(f"{api_prefix}/bookings", json=payload, headers=headers)


def test_the_conflict_response_carries_the_existing_booking(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = client.post(f"{api_prefix}/booths", json={"label": None}, headers=headers).json()[
        "id"
    ]

    first = _book(client, api_prefix, headers, ids, booth_id, 0)
    clash = _book(client, api_prefix, headers, ids, booth_id, 1, artist_id=ids["artist"])

    assert first.status_code == 201
    assert clash.status_code == 409

    body = clash.json()
    assert body["scope"] == "booth"
    assert body["conflicting_booking_id"] == first.json()["id"]
    assert body["detail"]


def test_an_ordinary_domain_error_stays_plain(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """So o conflito acrescenta campos. Um erro comum continua devolvendo
    apenas a mensagem -- a extensao e por dados, e nao um formato novo imposto a
    todas as respostas de erro."""
    _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/bookings/00000000-0000-0000-0000-000000000000/approve", headers=headers
    )

    assert response.status_code == 422
    assert set(response.json()) == {"detail"}
