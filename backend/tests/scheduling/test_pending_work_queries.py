"""As tres consultas do painel do gestor (RN-AGE-012 e secao 10.1).

O painel pergunta "o que esta esperando decisao", sem data e sem agendamento em
mao. Sem filtro por estado, cada uma dessas perguntas traria o historico inteiro
do estudio para o navegador filtrar -- custo que cresce toda semana sem ninguem
ter mudado nada, e que so aparece quando o estudio ja depende da tela.

O recorte por perfil continua valendo em cima do filtro: o artista que pede as
pendentes recebe as dele, nao as do estudio.
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from tests.support.account_builder import AccountBuilder
from tests.support.deposit_confirmer import DepositConfirmer

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


def _booth(client: TestClient, api_prefix: str, headers: dict[str, str]) -> str:
    response = client.post(f"{api_prefix}/booths", json={"label": None}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _book(
    client: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    ids: dict[str, str],
    booth_id: str,
    hours_offset: int,
    artist_id: str | None = None,
) -> str:
    start = START + timedelta(hours=hours_offset)
    payload: dict[str, object] = {
        "client_id": ids["client"],
        "booth_id": booth_id,
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=2)).isoformat(),
    }
    if artist_id:
        payload["artist_id"] = artist_id
    created = client.post(f"{api_prefix}/bookings", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    return created.json()["id"]


def _quote(client: TestClient, api_prefix: str, headers: dict[str, str], client_id: str) -> str:
    created = client.post(
        f"{api_prefix}/quotes",
        json={
            "client_id": client_id,
            "origin": "ARTIST_OWN",
            "description": "Blackwork forearm sleeve",
            "body_region": "Left forearm",
            "size_estimate": "20cm",
            "total_value": "1000.00",
            "planned_sessions": 4,
            "planned_value_per_session": "250.00",
            "estimated_duration_minutes": 180,
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


def test_pending_bookings_come_without_a_date_window(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-AGE-012: o painel pergunta o que espera decisao, nao o que ha hoje.

    Uma solicitacao esquecida e justamente a que ninguem foi procurar no dia
    certo -- exigir janela de data devolveria a dor ao gestor."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _booth(client, api_prefix, headers)
    pending = _book(client, api_prefix, headers, ids, booth_id, 0, ids["artist"])
    decided = _book(client, api_prefix, headers, ids, booth_id, 5, ids["other"])
    DepositConfirmer(client, api_prefix).confirm_for(decided, headers)
    client.post(f"{api_prefix}/bookings/{decided}/approve", headers=headers)

    response = client.get(f"{api_prefix}/bookings", params={"status": "REQUESTED"})

    assert response.status_code == 200, response.text
    assert [booking["id"] for booking in response.json()] == [pending]


def test_the_status_filter_keeps_the_artist_scope(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O filtro se soma ao recorte por perfil, nao o substitui."""
    ids = _setup(session)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _booth(client, api_prefix, owner)
    mine = _book(client, api_prefix, owner, ids, booth_id, 0, ids["artist"])
    _book(client, api_prefix, owner, ids, booth_id, 5, ids["other"])

    artist = TestClient(client.app)
    _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.get(f"{api_prefix}/bookings", params={"status": "REQUESTED"})

    assert response.status_code == 200, response.text
    assert [booking["id"] for booking in response.json()] == [mine]


def test_the_status_filter_and_the_date_window_are_independent(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Um pergunta quando, o outro em que situacao. Juntos, recortam os dois."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _booth(client, api_prefix, headers)
    inside = _book(client, api_prefix, headers, ids, booth_id, 0, ids["artist"])
    _book(client, api_prefix, headers, ids, booth_id, 100, ids["other"])

    response = client.get(
        f"{api_prefix}/bookings",
        params={
            "status": "REQUESTED",
            "starts_at": START.isoformat(),
            "ends_at": (START + timedelta(hours=10)).isoformat(),
        },
    )

    assert [booking["id"] for booking in response.json()] == [inside]


def test_an_unknown_status_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    _setup(session)
    _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.get(f"{api_prefix}/bookings", params={"status": "WAITING"})

    assert response.status_code == 422


def test_pending_quotes_come_filtered(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-002: orcamento nao vence sozinho. Fica pendente pelo tempo que for,
    e sem o painel nada cobra decisao."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    pending = _quote(client, api_prefix, headers, ids["client"])
    decided = _quote(client, api_prefix, headers, ids["client"])
    client.post(
        f"{api_prefix}/quotes/{decided}/reject",
        json={"reason": "The client changed the design."},
        headers=headers,
    )

    response = client.get(f"{api_prefix}/quotes", params={"status": "PENDING"})

    assert response.status_code == 200, response.text
    assert [quote["id"] for quote in response.json()] == [pending]


def test_payments_awaiting_confirmation_come_from_the_whole_studio(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Secao 10.1: a fila de trabalho do gestor nao parte de um agendamento.

    Desde a M5 o sinal nao confirmado trava a aprovacao (RN-AGE-005), entao
    esquecer um pagamento trava a agenda."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _booth(client, api_prefix, headers)
    waiting = _book(client, api_prefix, headers, ids, booth_id, 0, ids["artist"])
    settled = _book(client, api_prefix, headers, ids, booth_id, 5, ids["other"])
    deposits = DepositConfirmer(client, api_prefix)
    reported = deposits.register_for(waiting, headers)
    deposits.confirm_for(settled, headers)

    response = client.get(f"{api_prefix}/payments", params={"status": "REPORTED"})

    assert response.status_code == 200, response.text
    assert [payment["id"] for payment in response.json()] == [reported]


def test_the_artist_cannot_see_the_studio_payment_queue(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Confirmar recebimento e do gestor (RN-PAG-002), e a fila e dele."""
    ids = _setup(session)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    booth_id = _booth(client, api_prefix, owner)
    booking_id = _book(client, api_prefix, owner, ids, booth_id, 0, ids["artist"])
    DepositConfirmer(client, api_prefix).register_for(booking_id, owner)

    artist = TestClient(client.app)
    _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.get(f"{api_prefix}/payments", params={"status": "REPORTED"})

    assert response.status_code == 403
