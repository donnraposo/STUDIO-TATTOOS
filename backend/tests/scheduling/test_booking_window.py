"""Recorte por intervalo na listagem de agendamentos.

A agenda mostra um dia por vez. Sem recorte, abrir um dia traria o historico
inteiro do estudio, e o custo cresceria toda semana ate a tela ficar lenta sem
ninguem ter mudado nada.

O cenario que este arquivo protege e o do agendamento que **atravessa** a borda:
uma sessao das 19h as 21h pertence ao dia de terca, e um filtro escrito com
`inicio >= :de` a perderia em qualquer consulta que comecasse depois das 19h. E
o tipo de defeito que aparece como "sumiu um agendamento da agenda".
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"
TUESDAY = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _setup(session: Session) -> str:
    builder = AccountBuilder(session)
    owner = builder.create(email="owner@studio.ie", password=PASSWORD)
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=owner.id)
    session.add(subject)
    session.flush()
    session.commit()
    return str(subject.id)


def _create_booking(
    client: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    client_id: str,
    bench_id: str,
    start: datetime,
    hours: int = 2,
) -> None:
    response = client.post(
        f"{api_prefix}/bookings",
        json={
            "client_id": client_id,
            "bench_id": bench_id,
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=hours)).isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text


def _create_bench(client: TestClient, api_prefix: str, headers: dict[str, str]) -> str:
    response = client.post(f"{api_prefix}/benches", json={"label": "Window"}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _day_window(day: datetime) -> dict[str, str]:
    opening = day.replace(hour=10, minute=0)
    return {
        "starts_at": opening.isoformat(),
        "ends_at": (opening + timedelta(hours=10)).isoformat(),
    }


def test_the_window_keeps_a_booking_that_crosses_its_edge(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Sessao que comeca antes do recorte e termina dentro dele continua sendo
    daquele dia. O filtro usa sobreposicao, nao comparacao com o inicio."""
    client_id = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)
    _create_booking(client, api_prefix, headers, client_id, bench_id, TUESDAY, hours=3)

    late = client.get(
        f"{api_prefix}/bookings",
        params={
            "starts_at": (TUESDAY + timedelta(hours=2)).isoformat(),
            "ends_at": (TUESDAY + timedelta(hours=6)).isoformat(),
        },
    )

    assert late.status_code == 200
    assert len(late.json()) == 1


def test_the_window_leaves_out_another_day(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    client_id = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    bench_id = _create_bench(client, api_prefix, headers)
    _create_booking(client, api_prefix, headers, client_id, bench_id, TUESDAY)
    _create_booking(
        client, api_prefix, headers, client_id, bench_id, TUESDAY + timedelta(days=1)
    )

    today = client.get(f"{api_prefix}/bookings", params=_day_window(TUESDAY))
    both = client.get(f"{api_prefix}/bookings")

    assert len(today.json()) == 1
    assert len(both.json()) == 2


def test_half_a_window_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Meia janela seria armadilha silenciosa: quem informasse so o inicio
    receberia todo o futuro e leria isso como "o dia"."""
    _setup(session)
    _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.get(f"{api_prefix}/bookings", params={"starts_at": TUESDAY.isoformat()})

    assert response.status_code == 422


def test_a_window_that_ends_before_it_starts_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    _setup(session)
    _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.get(
        f"{api_prefix}/bookings",
        params={
            "starts_at": TUESDAY.isoformat(),
            "ends_at": (TUESDAY - timedelta(hours=1)).isoformat(),
        },
    )

    assert response.status_code == 422
