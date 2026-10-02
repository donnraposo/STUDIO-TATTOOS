"""Ciclo do repasse pela API (RN-REP-003 a RN-REP-007).

O que mais importa aqui e a visibilidade: "cada artista visualizara somente seus
proprios valores". O demonstrativo diz quanto alguem recebeu, e vazar isso entre
colegas e dano que nao se desfaz com um pedido de desculpas.

O segundo e a idempotencia do fechamento. Com calculo sob demanda, duas abas
abertas na tela de repasses sao dois processos -- e fechar duas vezes nao pode
dobrar o que o artista recebe.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from app.modules.quotes.domain.quote_origin import QuoteOrigin
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.domain.session_status import SessionStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession
from tests.support.account_builder import AccountBuilder

PASSWORD = "correct horse battery staple"
DUBLIN = ZoneInfo("Europe/Dublin")

#: Sexta, 25 de setembro de 2026, as 20h de Dublin.
#:
#: Uma semana **ja encerrada**: o fechamento sob demanda recusa semana em curso,
#: e um teste ancorado no futuro passaria a falhar sozinho ao chegar a data.
CLOSING = datetime(2026, 9, 25, 20, tzinfo=DUBLIN)
INSIDE_WEEK = datetime(2026, 9, 23, 15, tzinfo=DUBLIN)
AFTER_CLOSING = CLOSING + timedelta(hours=1)


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _setup(session: Session) -> dict[str, uuid.UUID]:
    builder = AccountBuilder(session)
    owner = builder.create(email="owner@studio.ie", password=PASSWORD)
    artist = builder.create(email="artist@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    other = builder.create(email="other@studio.ie", password=PASSWORD, role=UserRole.RESIDENT)
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    session.add(subject)
    session.flush()
    session.commit()
    return {
        "owner": owner.id,
        "artist": artist.id,
        "other": other.id,
        "client": subject.id,
    }


def _settled_session(
    session: Session,
    ids: dict[str, uuid.UUID],
    artist_id: uuid.UUID,
    charged: str,
    percentage: str,
    confirmed_at: datetime,
    status: SessionStatus = SessionStatus.PAID_OFF,
) -> TattooSession:
    """Uma sessao quitada, montada direto no banco.

    O caminho pela API exigiria orcamento, agendamento, sinal e confirmacao --
    quatro sprints de pre-condicao para testar a quinta. O que este arquivo
    exercita e o repasse, e a sessao quitada e a entrada dele."""
    quote = Quote(
        client_id=ids["client"],
        artist_id=artist_id,
        created_by=ids["owner"],
        origin=QuoteOrigin.ARTIST_OWN,
        description="Blackwork sleeve",
        body_region="Left forearm",
        size_estimate="20cm",
        total_value=Decimal("1000.00"),
        planned_sessions=4,
        planned_value_per_session=Decimal("250.00"),
        estimated_duration_minutes=180,
        status=QuoteStatus.APPROVED,
        artist_percentage=Decimal(percentage),
        approved_at=confirmed_at,
        approved_by=ids["owner"],
    )
    session.add(quote)
    session.flush()

    tattoo = TattooSession(
        quote_id=quote.id,
        sequence_number=1,
        status=status,
        origin=QuoteOrigin.ARTIST_OWN,
        planned_value=Decimal("250.00"),
        charged_value=Decimal(charged),
        artist_percentage=Decimal(percentage),
        performed_at=confirmed_at,
        marked_done_by=artist_id,
        confirmed_at=confirmed_at if status == SessionStatus.PAID_OFF else None,
        confirmed_by=ids["owner"] if status == SessionStatus.PAID_OFF else None,
    )
    session.add(tattoo)
    session.flush()
    session.commit()
    return tattoo


def _close(client: TestClient, api_prefix: str, headers: dict[str, str]):
    return client.post(
        f"{api_prefix}/payouts/close",
        json={"reference": INSIDE_WEEK.isoformat()},
        headers=headers,
    )


def test_the_week_closes_with_the_share_for_each_session(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-001 e RN-REP-007: 70% de EUR 250 sao EUR 175."""
    ids = _setup(session)
    _settled_session(session, ids, ids["artist"], "250.00", "70.00", INSIDE_WEEK)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _close(client, api_prefix, headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    assert body[0]["artist_id"] == str(ids["artist"])
    assert body[0]["gross_total"] == "175.00"
    assert body[0]["net_total"] == "175.00"
    assert body[0]["status"] == "CALCULATED"


def test_each_artist_gets_their_own_payout(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    _settled_session(session, ids, ids["artist"], "250.00", "70.00", INSIDE_WEEK)
    _settled_session(session, ids, ids["other"], "400.00", "50.00", INSIDE_WEEK)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    body = _close(client, api_prefix, headers).json()

    totals = {payout["artist_id"]: payout["net_total"] for payout in body}
    assert totals[str(ids["artist"])] == "175.00"
    assert totals[str(ids["other"])] == "200.00"


def test_closing_twice_does_not_double_the_payout(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Com calculo sob demanda, duas abas sao dois processos. Um repasse e
    fotografia: recalcular reescreveria o que o artista ja viu."""
    ids = _setup(session)
    _settled_session(session, ids, ids["artist"], "250.00", "70.00", INSIDE_WEEK)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    first = _close(client, api_prefix, headers).json()
    second = _close(client, api_prefix, headers).json()

    assert first[0]["id"] == second[0]["id"]
    assert second[0]["net_total"] == "175.00"
    statement = client.get(f"{api_prefix}/payouts/{first[0]['id']}").json()
    assert len(statement["items"]) == 1


def test_a_session_that_is_not_paid_off_stays_out(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-PAG-008: o repasse so e liberado depois de a sessao estar realizada e
    integralmente quitada. Pagar antes e pagar sobre dinheiro que o estudio
    ainda nao viu."""
    ids = _setup(session)
    _settled_session(
        session,
        ids,
        ids["artist"],
        "250.00",
        "70.00",
        INSIDE_WEEK,
        status=SessionStatus.DONE,
    )
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    assert _close(client, api_prefix, headers).json() == []


def test_a_session_from_another_week_stays_out(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-004: a semana vai de sexta 20h a sexta 20h."""
    ids = _setup(session)
    _settled_session(session, ids, ids["artist"], "250.00", "70.00", AFTER_CLOSING)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    assert _close(client, api_prefix, headers).json() == []


def test_a_week_that_has_not_closed_yet_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A regra diz que o sistema calcula **depois** do fechamento. Sem esta
    recusa, abrir a tela numa quarta fecharia a semana corrente pela metade, e o
    resto dos pagamentos cairia em lugar nenhum."""
    _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/payouts/close",
        json={"reference": (datetime.now(UTC) + timedelta(days=1)).isoformat()},
        headers=headers,
    )

    assert response.status_code == 422
    assert "closed" in response.json()["detail"].lower()


def test_the_artist_cannot_close_the_week(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Deixar o artista fechar o proprio repasse seria deixa-lo decidir quando
    recebe."""
    _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    assert _close(client, api_prefix, headers).status_code == 403


def test_the_artist_sees_only_their_own_payouts(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-004, a regra mais importante do modulo."""
    ids = _setup(session)
    _settled_session(session, ids, ids["artist"], "250.00", "70.00", INSIDE_WEEK)
    _settled_session(session, ids, ids["other"], "400.00", "50.00", INSIDE_WEEK)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    _close(client, api_prefix, owner)

    artist = TestClient(client.app)
    _sign_in(artist, api_prefix, "artist@studio.ie")
    mine = artist.get(f"{api_prefix}/payouts").json()

    assert len(mine) == 1
    assert mine[0]["artist_id"] == str(ids["artist"])


def test_the_artist_cannot_open_a_colleagues_statement(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    _settled_session(session, ids, ids["other"], "400.00", "50.00", INSIDE_WEEK)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    theirs = _close(client, api_prefix, owner).json()[0]

    artist = TestClient(client.app)
    _sign_in(artist, api_prefix, "artist@studio.ie")

    assert artist.get(f"{api_prefix}/payouts/{theirs['id']}").status_code == 403


def test_the_statement_shows_what_the_rule_requires(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-007: sessoes incluidas, valor recebido por sessao, percentual
    aplicado e total liquido."""
    ids = _setup(session)
    tattoo = _settled_session(session, ids, ids["artist"], "250.00", "70.00", INSIDE_WEEK)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    payout = _close(client, api_prefix, owner).json()[0]

    statement = client.get(f"{api_prefix}/payouts/{payout['id']}").json()

    assert statement["payout"]["net_total"] == "175.00"
    assert len(statement["items"]) == 1
    assert statement["items"][0]["session_id"] == str(tattoo.id)
    assert statement["items"][0]["received_amount"] == "250.00"
    assert statement["items"][0]["percentage"] == "70.00"
    assert statement["items"][0]["amount"] == "175.00"


def test_management_confirms_the_transfer(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-004: a confirmacao registra data, hora, valor e responsavel."""
    ids = _setup(session)
    _settled_session(session, ids, ids["artist"], "250.00", "70.00", INSIDE_WEEK)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    payout = _close(client, api_prefix, owner).json()[0]

    response = client.post(
        f"{api_prefix}/payouts/{payout['id']}/confirm-paid", json={}, headers=owner
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "PAID"
    assert response.json()["paid_at"] is not None
    assert response.json()["paid_by"] == str(ids["owner"])


def test_confirming_twice_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A segunda confirmacao reescreveria a data e o responsavel da primeira,
    apagando do historico quem de fato fez a transferencia."""
    ids = _setup(session)
    _settled_session(session, ids, ids["artist"], "250.00", "70.00", INSIDE_WEEK)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    payout = _close(client, api_prefix, owner).json()[0]
    client.post(f"{api_prefix}/payouts/{payout['id']}/confirm-paid", json={}, headers=owner)

    again = client.post(
        f"{api_prefix}/payouts/{payout['id']}/confirm-paid", json={}, headers=owner
    )

    assert again.status_code == 422


def test_the_artist_cannot_confirm_their_own_payout(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Deixar o artista confirmar seria deixa-lo declarar que recebeu."""
    ids = _setup(session)
    _settled_session(session, ids, ids["artist"], "250.00", "70.00", INSIDE_WEEK)
    owner = _sign_in(client, api_prefix, "owner@studio.ie")
    payout = _close(client, api_prefix, owner).json()[0]

    artist = TestClient(client.app)
    headers = _sign_in(artist, api_prefix, "artist@studio.ie")
    response = artist.post(
        f"{api_prefix}/payouts/{payout['id']}/confirm-paid", json={}, headers=headers
    )

    assert response.status_code == 403
