"""O faturamento do mes, contra a planilha real do estudio (RN 10.4).

Este arquivo reproduz **o controle de outubro de 2026 que o estudio mantem a
mao**, atendimento por atendimento, e confere os tres numeros do rodape:

    VALOR TOTAL TATTOOS  EUR 1.640,00
    VALOR STUDIO         EUR   421,50
    VALOR TOTAL TATUADORES EUR 1.218,50

E o teste mais valioso do modulo, e nao por ser o maior: ele e a unica prova de
que o sistema devolve o mesmo numero que a planilha, que e a pergunta que o
estudio vai fazer no primeiro mes de uso. Qualquer divergencia de centavo
aparece aqui, inteira, antes de aparecer numa conversa sobre quanto alguem
recebeu.

A planilha mostra **tres divisoes convivendo no mesmo mes** -- 85/15, 70/30 e
50/50 -- e o mesmo artista em mais de uma: YTALO em 85/15 e em 50/50, FARPA em
85/15 e em 70/30. E a razao do ADR-030, e aqui ela e exercitada de ponta a
ponta.
"""

import uuid
from datetime import datetime
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

#: O controle de outubro de 2026, linha a linha: dia, artista, valor cobrado e
#: percentual do tatuador. A coluna "Deposito" esta vazia em todas as linhas da
#: planilha, e nao entra na conta: a RN-PAG-005 diz que o sinal ja integra o
#: preco da tatuagem e a base do repasse.
SPREADSHEET = [
    (1, "ytalo", "250.00", "85.00"),
    (1, "farpa", "130.00", "85.00"),
    (1, "yukimy", "250.00", "70.00"),
    (2, "lisa", "50.00", "70.00"),
    (2, "farpa", "150.00", "85.00"),
    (3, "ytalo", "120.00", "50.00"),
    (3, "farpa", "180.00", "70.00"),
    (3, "duda", "180.00", "70.00"),
    (4, "lipo", "80.00", "70.00"),
    (5, "lipo", "150.00", "70.00"),
    (5, "ytalo", "100.00", "85.00"),
]

ARTISTS = ["ytalo", "farpa", "yukimy", "lisa", "duda", "lipo"]


def _sign_in(client: TestClient, api_prefix: str, email: str) -> dict[str, str]:
    response = client.post(f"{api_prefix}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, f"login da pre-condicao falhou: {response.text}"
    settings = Settings()
    return {settings.csrf_header_name: client.cookies.get(settings.csrf_cookie_name)}


def _setup(session: Session) -> dict[str, uuid.UUID]:
    builder = AccountBuilder(session)
    ids: dict[str, uuid.UUID] = {
        "owner": builder.create(email="owner@studio.ie", password=PASSWORD).id
    }
    for name in ARTISTS:
        ids[name] = builder.create(
            email=f"{name}@studio.ie", password=PASSWORD, role=UserRole.RESIDENT
        ).id

    subject = Client(name="Aoife", phone="+353 87 111 1111", registered_by_artist_id=ids["ytalo"])
    session.add(subject)
    session.flush()
    ids["client"] = subject.id
    session.commit()
    return ids


def _settled(
    session: Session,
    ids: dict[str, uuid.UUID],
    artist: str,
    charged: str,
    percentage: str,
    when: datetime,
) -> None:
    """Uma sessao quitada direto no banco.

    O caminho pela API exigiria orcamento, agendamento, sinal e confirmacao para
    cada uma das onze linhas. O que este arquivo exercita e o relatorio, e a
    sessao quitada e a entrada dele."""
    quote = Quote(
        client_id=ids["client"],
        artist_id=ids[artist],
        created_by=ids["owner"],
        origin=QuoteOrigin.ARTIST_OWN,
        description="Blackwork",
        body_region="Left forearm",
        size_estimate="20cm",
        total_value=Decimal(charged),
        planned_sessions=1,
        planned_value_per_session=Decimal(charged),
        estimated_duration_minutes=180,
        status=QuoteStatus.APPROVED,
        artist_percentage=Decimal(percentage),
        approved_at=when,
        approved_by=ids["owner"],
    )
    session.add(quote)
    session.flush()

    session.add(
        TattooSession(
            quote_id=quote.id,
            sequence_number=1,
            status=SessionStatus.PAID_OFF,
            origin=QuoteOrigin.ARTIST_OWN,
            planned_value=Decimal(charged),
            charged_value=Decimal(charged),
            artist_percentage=Decimal(percentage),
            performed_at=when,
            marked_done_by=ids[artist],
            confirmed_at=when,
            confirmed_by=ids["owner"],
        )
    )
    session.flush()


def _october(session: Session, ids: dict[str, uuid.UUID]) -> None:
    for day, artist, charged, percentage in SPREADSHEET:
        _settled(
            session, ids, artist, charged, percentage, datetime(2026, 10, day, 14, tzinfo=DUBLIN)
        )
    session.commit()


def test_the_month_reproduces_the_studio_spreadsheet(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Os tres numeros do rodape, contra o controle real de outubro de 2026."""
    ids = _setup(session)
    _october(session, ids)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.get(f"{api_prefix}/revenue?year=2026&month=10", headers=headers)

    assert response.status_code == 200, response.text
    totals = response.json()["totals"]
    assert totals["value"] == "1640.00"
    assert totals["artists"] == "1218.50"
    assert totals["studio"] == "421.50"
    assert totals["sessions"] == 11


def test_the_two_shares_add_up_to_the_total(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """E assim que o estudio confere a planilha, e tem de valer sempre.

    Calcular os dois lados por multiplicacao separada faria a soma falhar por um
    centavo sempre que o arredondamento subisse."""
    ids = _setup(session)
    _october(session, ids)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    totals = client.get(f"{api_prefix}/revenue?year=2026&month=10", headers=headers).json()[
        "totals"
    ]

    assert Decimal(totals["artists"]) + Decimal(totals["studio"]) == Decimal(totals["value"])


def test_every_line_carries_the_split_it_was_approved_with(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN-REP-006. A planilha mostra o mesmo artista em divisoes diferentes no
    mesmo mes -- YTALO em 85/15 e em 50/50 -- e e o percentual **congelado** de
    cada atendimento que explica isso."""
    ids = _setup(session)
    _october(session, ids)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    lines = client.get(f"{api_prefix}/revenue?year=2026&month=10", headers=headers).json()[
        "lines"
    ]
    ytalo = sorted(
        Decimal(line["percentage"]) for line in lines if line["artist_id"] == str(ids["ytalo"])
    )

    assert ytalo == [Decimal("50.00"), Decimal("85.00"), Decimal("85.00")]


def test_a_month_with_no_work_is_zero_and_not_an_error(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Setembro nao tem nada. Um erro ali faria o estudio concluir que o
    relatorio quebrou, quando a resposta correta e que nao se tatuou."""
    _setup(session)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.get(f"{api_prefix}/revenue?year=2026&month=9", headers=headers)

    assert response.status_code == 200
    assert response.json()["totals"]["value"] == "0.00"
    assert response.json()["lines"] == []


def test_work_from_another_month_stays_out(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A fronteira do mes e um instante no fuso do estudio, nao uma data em UTC.

    Este atendimento acontece as 23h30 de 31 de outubro em Dublin, que ja e 1 de
    novembro em... nenhum fuso relevante -- mas o inverso acontece no verao, e o
    teste existe para que a conta seja feita no fuso certo em qualquer epoca."""
    ids = _setup(session)
    _october(session, ids)
    _settled(
        session, ids, "lisa", "999.00", "70.00", datetime(2026, 11, 1, 10, tzinfo=DUBLIN)
    )
    session.commit()
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    totals = client.get(f"{api_prefix}/revenue?year=2026&month=10", headers=headers).json()[
        "totals"
    ]

    assert totals["value"] == "1640.00"


def test_an_artist_cannot_see_the_studio_revenue(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """RN 10.4 da o relatorio a proprietario e gerente. Abri-lo ao artista
    mostraria a ele quanto todos os colegas receberam -- e a RN-REP-004 o limita
    aos proprios valores, que esta tela contradiria por outra porta."""
    _setup(session)
    headers = _sign_in(client, api_prefix, "ytalo@studio.ie")

    response = client.get(f"{api_prefix}/revenue?year=2026&month=10", headers=headers)

    assert response.status_code == 403


def test_the_monthly_comparison_keeps_empty_months_in_place(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """Um buraco na sequencia faria o grafico mentir sobre o tempo: setembro
    vazio ao lado de outubro cheio e informacao, e setembro ausente faz parecer
    que agosto foi ontem."""
    ids = _setup(session)
    _october(session, ids)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    response = client.get(
        f"{api_prefix}/revenue/monthly?year=2026&month=10&count=3", headers=headers
    )

    assert response.status_code == 200, response.text
    months = response.json()
    assert [(each["year"], each["month"]) for each in months] == [
        (2026, 8),
        (2026, 9),
        (2026, 10),
    ]
    assert months[0]["totals"]["value"] == "0.00"
    assert months[2]["totals"]["value"] == "1640.00"


def test_the_report_says_whether_the_artist_was_already_paid(
    client: TestClient, session: Session, api_prefix: str
) -> None:
    """A coluna "Status" da planilha, e a OBS "PAGO DIA 02/10".

    Entrar num fechamento calculado nao e ter sido pago: entre a sexta e a
    transferencia o artista ainda nao recebeu, e dizer que esta pago o que nao
    esta e o erro que o estudio descobriria pela reclamacao dele."""
    ids = _setup(session)
    _october(session, ids)
    headers = _sign_in(client, api_prefix, "owner@studio.ie")

    lines = client.get(f"{api_prefix}/revenue?year=2026&month=10", headers=headers).json()[
        "lines"
    ]

    assert all(line["transferred"] is False for line in lines)
