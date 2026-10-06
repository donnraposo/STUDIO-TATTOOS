"""O acordo de percentual por artista (ADR-030, RN-CLI-003 e RN-REP-006).

A planilha de controle do estudio mostra tres divisoes no mesmo mes -- 85/15,
70/30 e 50/50 -- e o mesmo artista em mais de uma. Tratar isso como excecao no
codigo obrigaria uma versao nova do sistema a cada acordo novo.

O que mais importa aqui e a RN-REP-006: mudar o acordo **nao pode** alcancar
trabalho ja aprovado. O artista aprovou sob 85% e recebe 85%, mesmo que o
estudio renegocie no dia seguinte.
"""

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.clients.infrastructure.models.client import Client
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
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    session.add(subject)
    session.flush()
    session.commit()
    return {"owner": str(owner.id), "artist": str(artist.id), "client": str(subject.id)}


def _quote(
    client: TestClient, api_prefix: str, headers: dict[str, str], ids: dict[str, str]
) -> str:
    created = client.post(
        f"{api_prefix}/quotes",
        json={
            "client_id": ids["client"],
            "artist_id": ids["artist"],
            "origin": "ARTIST_OWN",
            "description": "Blackwork sleeve",
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


def _set_percentage(
    client: TestClient,
    api_prefix: str,
    headers: dict[str, str],
    artist_id: str,
    percentage: str | None,
):
    return client.put(
        f"{api_prefix}/users/{artist_id}/percentage",
        json={"percentage": percentage},
        headers=headers,
    )


def test_an_artist_starts_without_an_agreement(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Nulo significa "use a regra da origem". Os artistas existentes seguem em
    70/30 ou 50/50 sem que ninguem preencha nada."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    accounts = client.get(f"{api_prefix}/users", headers=headers).json()
    artist = next(a for a in accounts if a["id"] == ids["artist"])

    assert artist["default_artist_percentage"] is None


def test_management_sets_the_agreement(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Os 85% que a planilha do estudio mostra, e que a tabela de origens nao
    tem."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _set_percentage(client, api_prefix, headers, ids["artist"], "85.00")

    assert response.status_code == 200, response.text
    assert response.json()["default_artist_percentage"] == "85.00"


def test_the_agreement_wins_over_the_origin_default(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Cliente proprio daria 70% pela RN-REP-001; o acordo da 85%.

    Um acordo negociado e mais especifico que uma regra geral."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    _set_percentage(client, api_prefix, headers, ids["artist"], "85.00")
    quote_id = _quote(client, api_prefix, headers, ids)

    approved = client.post(
        f"{api_prefix}/quotes/{quote_id}/approve",
        json={"artist_percentage": None},
        headers=headers,
    )

    assert approved.status_code == 200, approved.text
    assert approved.json()["artist_percentage"] == "85.00"


def test_an_explicit_correction_still_wins_over_the_agreement(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-003: o gestor corrige o percentual **deste** atendimento. A ordem
    e: correcao pontual, depois acordo do artista, depois regra da origem."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    _set_percentage(client, api_prefix, headers, ids["artist"], "85.00")
    quote_id = _quote(client, api_prefix, headers, ids)

    approved = client.post(
        f"{api_prefix}/quotes/{quote_id}/approve",
        json={"artist_percentage": "50.00"},
        headers=headers,
    )

    assert approved.json()["artist_percentage"] == "50.00"


def test_changing_the_agreement_does_not_reach_approved_work(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-006, e e o teste que mais importa deste arquivo.

    O artista aprovou sob 85% e recebe 85%, mesmo que o estudio renegocie no dia
    seguinte. A garantia nao esta no caso de uso que altera: esta na copia que o
    orcamento congelou."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    _set_percentage(client, api_prefix, headers, ids["artist"], "85.00")
    quote_id = _quote(client, api_prefix, headers, ids)
    client.post(
        f"{api_prefix}/quotes/{quote_id}/approve",
        json={"artist_percentage": None},
        headers=headers,
    )

    _set_percentage(client, api_prefix, headers, ids["artist"], "50.00")

    quote = client.get(f"{api_prefix}/quotes/{quote_id}", headers=headers).json()
    assert quote["artist_percentage"] == "85.00"
    sessions = client.get(f"{api_prefix}/quotes/{quote_id}/sessions", headers=headers).json()
    assert {s["artist_percentage"] for s in sessions} == {"85.00"}


def test_clearing_the_agreement_returns_to_the_origin_rule(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """E assim que um acordo e encerrado, e nao apagando a conta."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    _set_percentage(client, api_prefix, headers, ids["artist"], "85.00")
    _set_percentage(client, api_prefix, headers, ids["artist"], None)
    quote_id = _quote(client, api_prefix, headers, ids)

    approved = client.post(
        f"{api_prefix}/quotes/{quote_id}/approve",
        json={"artist_percentage": None},
        headers=headers,
    )

    assert approved.json()["artist_percentage"] == "70.00"


def test_the_artist_cannot_set_their_own_share(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Deixar o artista mexer seria deixa-lo escrever o proprio contrato."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = _set_percentage(client, api_prefix, headers, ids["artist"], "100.00")

    assert response.status_code == 403


def test_a_share_outside_the_range_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    assert _set_percentage(client, api_prefix, headers, ids["artist"], "0").status_code == 422
    assert _set_percentage(client, api_prefix, headers, ids["artist"], "101").status_code == 422


def test_an_account_that_does_not_tattoo_has_no_share(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Gerente que nao atua como tatuador nao tem repasse, e dar-lhe um
    percentual criaria um acordo que nunca sera usado."""
    ids = _setup(session)
    builder = AccountBuilder(session)
    manager = builder.create(
        email="manager@studio.ie", password=PASSWORD, role=UserRole.MANAGER
    )
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = _set_percentage(client, api_prefix, headers, str(manager.id), "70.00")

    assert response.status_code == 422
    # O artista continua sem acordo: a recusa nao mexeu em ninguem.
    accounts = client.get(f"{api_prefix}/users", headers=headers).json()
    artist = next(a for a in accounts if a["id"] == ids["artist"])
    assert artist["default_artist_percentage"] is None


def test_the_agreement_is_recorded_with_the_previous_value(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Mudar sem registro seria mudar o contrato de alguem em silencio."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")
    _set_percentage(client, api_prefix, headers, ids["artist"], "85.00")
    _set_percentage(client, api_prefix, headers, ids["artist"], "70.00")

    trail = session.execute(
        text(
            "SELECT old_values, new_values FROM audit_log"
            " WHERE action = 'ARTIST_PERCENTAGE_SET' AND entity_id = :id"
            " ORDER BY created_at DESC LIMIT 1"
        ),
        {"id": ids["artist"]},
    ).one()

    assert trail[0]["default_artist_percentage"] == "85.00"
    assert trail[1]["default_artist_percentage"] == "70.00"
