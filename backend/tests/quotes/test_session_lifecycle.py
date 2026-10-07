"""Ciclo da sessão pela API (RN-ORC-005 e RN-ORC-006).

O cenário que mais importa aqui é a separação entre **realizada** e
**concluída**. O artista marca que a sessão aconteceu; o gestor confirma quanto
entrou. Se um único ato fizesse as duas coisas, trabalho ainda não pago entraria
em repasse — e o erro só apareceria no fechamento da sexta-feira.

O segundo é o ajuste da RN-ORC-006: quando o que sobra deixa de fechar com o
valor aprovado, o orçamento volta a pendente e o percentual congelado é
descartado, pelo mesmo motivo da edição (RN-REP-006).
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


def _quote_payload(client_id: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
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
    payload.update(overrides)
    return payload


def _approved_quote(
    client: TestClient, api_prefix: str, ids: dict[str, str], **overrides: object
) -> str:
    """Um orçamento aprovado, que é a pré-condição de qualquer sessão existir."""
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    created = client.post(
        f"{api_prefix}/quotes", json=_quote_payload(ids["client"], **overrides), headers=headers
    )
    assert created.status_code == 201, created.text
    quote_id = created.json()["id"]

    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    approved = client.post(
        f"{api_prefix}/quotes/{quote_id}/approve", json={"artist_percentage": None},
        headers=manager,
    )
    assert approved.status_code == 200, approved.text
    return quote_id


def _sessions(client: TestClient, api_prefix: str, quote_id: str) -> list[dict[str, object]]:
    response = client.get(f"{api_prefix}/quotes/{quote_id}/sessions")
    assert response.status_code == 200, response.text
    return response.json()


def test_approval_generates_the_planned_sessions(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-005: as sessões nascem da aprovação, com o acordo copiado.

    `origin` e `artist_percentage` são cópias congeladas (RN-REP-006): é delas
    que o repasse vai ler, e não do orçamento na data do cálculo."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)

    records = _sessions(client, api_prefix, quote_id)

    assert [record["sequence_number"] for record in records] == [1, 2, 3, 4]
    assert {record["status"] for record in records} == {"SCHEDULED"}
    assert {record["planned_value"] for record in records} == {"250.00"}
    assert {record["artist_percentage"] for record in records} == {"70.00"}
    assert {record["origin"] for record in records} == {"ARTIST_OWN"}


def test_a_pending_quote_has_no_sessions(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    created = client.post(
        f"{api_prefix}/quotes", json=_quote_payload(ids["client"]), headers=headers
    )

    assert _sessions(client, api_prefix, created.json()["id"]) == []


def test_reapproval_keeps_what_was_done_and_refreshes_only_the_scheduled(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A reaprovação não pode apagar trabalho executado nem manter o plano
    velho. Mantém a sessão realizada e recria as agendadas pelo plano novo."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(f"{api_prefix}/sessions/{first}/mark-done", json={}, headers=artist)

    # Quem edita um orçamento já aprovado é o gestor: a RN-ORC-003 só deixa o
    # artista mexer enquanto pendente, e o backend recusa o residente com 403.
    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    edited = client.put(
        f"{api_prefix}/quotes/{quote_id}",
        json={
            "origin": "ARTIST_OWN",
            "description": "Blackwork forearm sleeve",
            "body_region": "Left forearm",
            "size_estimate": "20cm",
            "total_value": "900.00",
            "planned_sessions": 3,
            "planned_value_per_session": "300.00",
            "estimated_duration_minutes": 180,
        },
        headers=manager,
    )
    assert edited.status_code == 200, edited.text
    reapproved = client.post(
        f"{api_prefix}/quotes/{quote_id}/approve", json={"artist_percentage": None},
        headers=manager,
    )
    assert reapproved.status_code == 200, reapproved.text

    records = _sessions(client, api_prefix, quote_id)
    assert [record["sequence_number"] for record in records] == [1, 2, 3]
    assert records[0]["status"] == "DONE"
    assert records[0]["planned_value"] == "250.00"
    assert [record["planned_value"] for record in records[1:]] == ["300.00", "300.00"]


def test_artist_marks_the_session_as_performed(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-005: quem marca é quem tatuou, e marcar não conclui."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]

    response = client.post(f"{api_prefix}/sessions/{first}/mark-done", json={}, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "DONE"
    assert body["performed_at"] is not None
    assert body["charged_value"] is None
    assert body["confirmed_at"] is None


def test_another_artist_cannot_mark_a_session_of_someone_else(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    headers = _sign_in(client, api_prefix, "other@studio.ie")

    response = client.post(f"{api_prefix}/sessions/{first}/mark-done", json={}, headers=headers)

    assert response.status_code == 403


def test_partial_session_records_what_was_actually_charged(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-006: o repasse incide sobre o recebido, não sobre o previsto."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]

    response = client.post(
        f"{api_prefix}/sessions/{first}/mark-done",
        json={"charged_value": "100.00"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "PARTIALLY_DONE"
    assert response.json()["charged_value"] == "100.00"


def test_a_partial_session_must_be_charged_less_than_planned(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Aceitar o valor previsto marcaria como interrompida uma sessão inteira, e
    o repasse sairia certo por acaso enquanto o histórico contaria outra coisa."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]

    response = client.post(
        f"{api_prefix}/sessions/{first}/mark-done",
        json={"charged_value": "250.00"},
        headers=headers,
    )

    assert response.status_code == 422


def test_artist_cannot_confirm_the_payment(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-005: deixar o artista confirmar o próprio recebimento seria
    deixá-lo liberar o próprio pagamento."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(f"{api_prefix}/sessions/{first}/mark-done", json={}, headers=headers)

    response = client.post(
        f"{api_prefix}/sessions/{first}/confirm-payment", json={}, headers=headers
    )

    assert response.status_code == 403


def test_manager_confirms_and_the_session_is_concluded(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-005: só depois da confirmação a sessão entra em repasse."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(f"{api_prefix}/sessions/{first}/mark-done", json={}, headers=artist)

    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    response = client.post(
        f"{api_prefix}/sessions/{first}/confirm-payment", json={}, headers=manager
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "PAID_OFF"
    assert body["charged_value"] == "250.00"
    assert body["confirmed_at"] is not None
    assert body["confirmed_by"] == ids["owner"]


def test_a_scheduled_session_cannot_be_confirmed(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]

    response = client.post(
        f"{api_prefix}/sessions/{first}/confirm-payment", json={}, headers=manager
    )

    assert response.status_code == 422


def test_correcting_the_value_without_a_reason_is_refused(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-005: correções ficam registradas com motivo. Correção silenciosa
    de valor é a diferença entre um acerto e um desvio, e sem o motivo escrito
    nenhuma das duas se distingue da outra."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(
        f"{api_prefix}/sessions/{first}/mark-done",
        json={"charged_value": "100.00"},
        headers=artist,
    )

    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    response = client.post(
        f"{api_prefix}/sessions/{first}/confirm-payment",
        json={"charged_value": "150.00"},
        headers=manager,
    )

    assert response.status_code == 422


def test_correcting_the_value_with_a_reason_is_recorded(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(
        f"{api_prefix}/sessions/{first}/mark-done",
        json={"charged_value": "100.00"},
        headers=artist,
    )

    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    response = client.post(
        f"{api_prefix}/sessions/{first}/confirm-payment",
        json={"charged_value": "150.00", "reason": "The client paid the rest in cash."},
        headers=manager,
    )

    assert response.status_code == 200, response.text
    assert response.json()["charged_value"] == "150.00"

    recorded = session.execute(
        text(
            "SELECT reason FROM audit_log"
            " WHERE action = 'SESSION_PAYMENT_CONFIRMED' AND entity_id = :id"
        ),
        {"id": first},
    ).scalar_one()
    assert recorded == "The client paid the rest in cash."


def test_a_confirmed_session_cannot_be_marked_again(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Desfazer uma confirmação de recebimento é ato do gestor, não do artista."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(f"{api_prefix}/sessions/{first}/mark-done", json={}, headers=artist)
    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    client.post(f"{api_prefix}/sessions/{first}/confirm-payment", json={}, headers=manager)

    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    response = client.post(f"{api_prefix}/sessions/{first}/mark-done", json={}, headers=artist)

    assert response.status_code == 422


def test_artist_cannot_adjust_the_remaining_sessions(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-006: o ajuste é de gerente ou proprietário."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = client.post(
        f"{api_prefix}/quotes/{quote_id}/sessions/adjust",
        json={"planned_values": ["300.00"]},
        headers=headers,
    )

    assert response.status_code == 403


def test_adjustment_that_keeps_the_total_leaves_the_quote_approved(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Uma sessão parcial de 100 sobre 250, e o que falta redistribuído de forma
    a fechar os mesmos 1000: nada precisa ser reaprovado."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(
        f"{api_prefix}/sessions/{first}/mark-done",
        json={"charged_value": "100.00"},
        headers=artist,
    )

    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    response = client.post(
        f"{api_prefix}/quotes/{quote_id}/sessions/adjust",
        json={"planned_values": ["300.00", "300.00", "300.00"]},
        headers=manager,
    )

    assert response.status_code == 200, response.text
    quote = client.get(f"{api_prefix}/quotes/{quote_id}").json()
    assert quote["status"] == "APPROVED"
    assert quote["artist_percentage"] == "70.00"


def test_adjustment_that_changes_the_total_sends_the_quote_back_to_pending(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-006 e RN-REP-006: mudou o valor comprometido, o acordo congelado
    deixa de valer e o orçamento exige nova aprovação."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(
        f"{api_prefix}/sessions/{first}/mark-done",
        json={"charged_value": "100.00"},
        headers=artist,
    )

    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    response = client.post(
        f"{api_prefix}/quotes/{quote_id}/sessions/adjust",
        json={"planned_values": ["250.00", "250.00"]},
        headers=manager,
    )

    assert response.status_code == 200, response.text
    quote = client.get(f"{api_prefix}/quotes/{quote_id}").json()
    assert quote["status"] == "PENDING"
    assert quote["artist_percentage"] is None
    assert quote["approved_at"] is None


def test_adjustment_counts_the_charged_value_of_a_partial_session(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Somar o previsto de uma parcial contaria dinheiro que não entrou. Aqui o
    plano restante repõe exatamente os 250 previstos, e mesmo assim o total cai
    para 1000 - 150, que é o que a parcial deixou de cobrar."""
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    artist = _sign_in(client, api_prefix, "artist@studio.ie")
    first = _sessions(client, api_prefix, quote_id)[0]["id"]
    client.post(
        f"{api_prefix}/sessions/{first}/mark-done",
        json={"charged_value": "100.00"},
        headers=artist,
    )

    manager = _sign_in(client, api_prefix, "owner@studio.ie")
    client.post(
        f"{api_prefix}/quotes/{quote_id}/sessions/adjust",
        json={"planned_values": ["250.00", "250.00", "250.00"]},
        headers=manager,
    )

    assert client.get(f"{api_prefix}/quotes/{quote_id}").json()["status"] == "PENDING"


def test_adjustment_refuses_a_session_worth_nothing(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    manager = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.post(
        f"{api_prefix}/quotes/{quote_id}/sessions/adjust",
        json={"planned_values": ["0.00"]},
        headers=manager,
    )

    assert response.status_code == 422


def test_another_artist_cannot_see_the_sessions(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    quote_id = _approved_quote(client, api_prefix, ids)
    _sign_in(client, api_prefix, "other@studio.ie")

    response = client.get(f"{api_prefix}/quotes/{quote_id}/sessions")

    assert response.status_code == 403
