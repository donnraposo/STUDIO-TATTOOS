"""Ciclo do orçamento pela API (RN-ORC-001 a RN-ORC-004 e RN-REP-006).

O cenário que mais importa aqui é o da edição de um orçamento aprovado. Ele
junta duas regras que, separadas, parecem inofensivas: alterar devolve a
Pendente (RN-ORC-003) e o percentual é congelado na aprovação (RN-REP-006). Se a
volta a pendente não limpar o percentual, a próxima aprovação pode passar sem
regravá-lo e o trabalho novo sai com o acordo velho.
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
    guest = builder.create(email="guest@studio.ie", password=PASSWORD, role=UserRole.GUEST)
    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=artist.id)
    session.add(subject)
    session.flush()
    session.commit()
    return {
        "owner": str(owner.id),
        "artist": str(artist.id),
        "other": str(other.id),
        "guest": str(guest.id),
        "client": str(subject.id),
    }


def _quote_fields(**overrides: object) -> dict[str, object]:
    """Os campos editáveis, que servem à edição e são a base da criação —
    o mesmo desenho de `QuoteFieldsRequest` e `QuoteRequest`."""
    fields: dict[str, object] = {
        "origin": "ARTIST_OWN",
        "description": "Blackwork forearm sleeve",
        "body_region": "Left forearm",
        "size_estimate": "20cm",
        "total_value": "1000.00",
        "planned_sessions": 4,
        "planned_value_per_session": "250.00",
        "estimated_duration_minutes": 180,
    }
    fields.update(overrides)
    return fields


def _quote_payload(client_id: str, **overrides: object) -> dict[str, object]:
    return {"client_id": client_id, **_quote_fields(**overrides)}


def _create_quote(
    caller: TestClient, api_prefix: str, headers: dict[str, str], payload: dict[str, object]
) -> str:
    response = caller.post(f"{api_prefix}/quotes", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_resident_creates_a_pending_quote_without_percentage(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-002: nasce pendente. RN-REP-006: percentual só existe aprovado."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")

    response = client.post(
        f"{api_prefix}/quotes", json=_quote_payload(ids["client"]), headers=headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["artist_percentage"] is None


def test_guest_cannot_create_a_quote(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-001: o guest não tem acesso ao módulo de orçamentos.

    O guest tatua, então qualquer verificação baseada em 'atua como artista' o
    deixaria passar. É por isso que a política confere o perfil."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "guest@studio.ie")

    response = client.post(
        f"{api_prefix}/quotes", json=_quote_payload(ids["client"]), headers=headers
    )

    assert response.status_code == 403


def test_resident_cannot_approve_a_quote(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-002: aprovar é do gestor, inclusive o próprio orçamento."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, _quote_payload(ids["client"]))

    response = client.post(f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=headers)

    assert response.status_code == 403


def test_approval_freezes_seventy_percent_for_the_artists_own_client(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-001: cliente próprio fica em 70% para o artista."""
    ids = _setup(session)
    artist_headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, artist_headers, _quote_payload(ids["client"]))

    owner = TestClient(client.app)
    owner_headers = _sign_in(owner, api_prefix, "owner@studio.ie")
    response = owner.post(
        f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=owner_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "APPROVED"
    assert body["artist_percentage"] == "70.00"
    assert body["approved_at"] is not None


def test_approval_freezes_fifty_percent_for_a_studio_referral(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-002: indicação do estúdio divide ao meio."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    quote_id = _create_quote(
        client,
        api_prefix,
        owner_headers,
        _quote_payload(ids["client"], origin="STUDIO_REFERRAL", artist_id=ids["artist"]),
    )

    response = client.post(
        f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=owner_headers
    )

    assert response.status_code == 200
    assert response.json()["artist_percentage"] == "50.00"


def test_management_can_correct_the_percentage_on_approval(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-CLI-003: só o gestor corrige o percentual, e vale para este atendimento.

    A auditoria guarda o percentual aplicado junto do padrão da origem: um
    acordo fora do padrão precisa ser rastreável."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    quote_id = _create_quote(client, api_prefix, owner_headers, _quote_payload(ids["client"]))

    response = client.post(
        f"{api_prefix}/quotes/{quote_id}/approve",
        json={"artist_percentage": "60.00"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert response.json()["artist_percentage"] == "60.00"

    recorded = session.execute(
        text(
            "SELECT new_values FROM audit_log WHERE action = 'QUOTE_APPROVED'"
            " AND entity_id = :id"
        ),
        {"id": quote_id},
    ).scalar_one()
    assert recorded["artist_percentage"] == "60.00"
    assert recorded["standard_for_origin"] == "70.00"


def test_editing_an_approved_quote_returns_it_to_pending_and_drops_the_percentage(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-003 e RN-REP-006 juntas, que é onde o erro se esconderia.

    Um percentual sobrevivente num orçamento pendente pareceria inofensivo, e
    permitiria à próxima aprovação passar sem regravá-lo — aplicando o acordo
    antigo a um valor novo."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    quote_id = _create_quote(client, api_prefix, owner_headers, _quote_payload(ids["client"]))
    client.post(f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=owner_headers)

    response = client.put(
        f"{api_prefix}/quotes/{quote_id}",
        json=_quote_fields(total_value="1600.00", planned_value_per_session="400.00"),
        headers=owner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["artist_percentage"] is None
    assert body["approved_at"] is None
    assert body["total_value"] == "1600.00"


def test_resident_cannot_edit_an_already_approved_quote(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Se pudesse, derrubaria a aprovação sozinho pelo ato de editar."""
    ids = _setup(session)
    artist_headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, artist_headers, _quote_payload(ids["client"]))

    owner = TestClient(client.app)
    owner_headers = _sign_in(owner, api_prefix, "owner@studio.ie")
    owner.post(f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=owner_headers)

    response = client.put(
        f"{api_prefix}/quotes/{quote_id}",
        json=_quote_fields(total_value="1600.00"),
        headers=artist_headers,
    )

    assert response.status_code == 403


def test_resident_edits_own_pending_quote(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-003: enquanto pendente, o residente corrige o próprio orçamento."""
    ids = _setup(session)
    headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, headers, _quote_payload(ids["client"]))

    response = client.put(
        f"{api_prefix}/quotes/{quote_id}",
        json=_quote_fields(description="Blackwork sleeve with negative space"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Blackwork sleeve with negative space"


def test_rejection_requires_a_reason(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-ORC-003: a recusa exige motivo; um campo vazio não é motivo."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    quote_id = _create_quote(client, api_prefix, owner_headers, _quote_payload(ids["client"]))

    missing = client.post(
        f"{api_prefix}/quotes/{quote_id}/reject", json={}, headers=owner_headers
    )
    empty = client.post(
        f"{api_prefix}/quotes/{quote_id}/reject", json={"reason": ""}, headers=owner_headers
    )

    assert missing.status_code == 422
    assert empty.status_code == 422


def test_management_rejects_with_reason_and_optional_note(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    quote_id = _create_quote(client, api_prefix, owner_headers, _quote_payload(ids["client"]))

    response = client.post(
        f"{api_prefix}/quotes/{quote_id}/reject",
        json={"reason": "Value below the studio minimum for this size"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["rejection_reason"] == "Value below the studio minimum for this size"
    assert body["rejection_note"] is None


def test_an_edited_rejected_quote_goes_back_to_pending(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Recusado não é fim de caminho: corrigir é como se submete de novo."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    quote_id = _create_quote(client, api_prefix, owner_headers, _quote_payload(ids["client"]))
    client.post(
        f"{api_prefix}/quotes/{quote_id}/reject",
        json={"reason": "Value below the studio minimum"},
        headers=owner_headers,
    )

    response = client.put(
        f"{api_prefix}/quotes/{quote_id}",
        json=_quote_fields(total_value="1800.00"),
        headers=owner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["rejection_reason"] is None


def test_a_decided_quote_cannot_be_approved_again(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Aprovar duas vezes regravaria a data e o responsável da decisão."""
    ids = _setup(session)
    owner_headers = _sign_in(client, api_prefix, "owner@studio.ie")
    quote_id = _create_quote(client, api_prefix, owner_headers, _quote_payload(ids["client"]))
    client.post(f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=owner_headers)

    response = client.post(
        f"{api_prefix}/quotes/{quote_id}/approve", json={}, headers=owner_headers
    )

    assert response.status_code == 422


def test_an_artist_does_not_see_another_artists_quote(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """O orçamento carrega valor e percentual do atendimento de outra pessoa."""
    ids = _setup(session)
    artist_headers = _sign_in(client, api_prefix, "artist@studio.ie")
    quote_id = _create_quote(client, api_prefix, artist_headers, _quote_payload(ids["client"]))

    other = TestClient(client.app)
    other_headers = _sign_in(other, api_prefix, "other@studio.ie")

    detail = other.get(f"{api_prefix}/quotes/{quote_id}", headers=other_headers)
    listing = other.get(f"{api_prefix}/quotes", headers=other_headers)

    assert detail.status_code == 403
    assert listing.json() == []


def test_management_sees_every_quote(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    ids = _setup(session)
    artist_headers = _sign_in(client, api_prefix, "artist@studio.ie")
    _create_quote(client, api_prefix, artist_headers, _quote_payload(ids["client"]))

    owner = TestClient(client.app)
    owner_headers = _sign_in(owner, api_prefix, "owner@studio.ie")
    listing = owner.get(f"{api_prefix}/quotes", headers=owner_headers)

    assert listing.status_code == 200
    assert len(listing.json()) == 1
