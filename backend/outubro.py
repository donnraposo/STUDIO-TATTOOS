"""Lanca o controle de outubro de 2026 do estudio no banco de desenvolvimento.

Onze atendimentos quitados, com o percentual congelado de cada um. Serve para a
tela de faturamento ter o que mostrar; nao e seed oficial.
"""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.container import Container
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.clients.infrastructure.models.client import Client
from app.modules.quotes.domain.quote_origin import QuoteOrigin
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.domain.session_status import SessionStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession

DUBLIN = ZoneInfo("Europe/Dublin")

ROWS = [
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

container = Container()
with container.database.session() as session:
    owner = session.execute(
        select(UserAccount).where(UserAccount.email == "owner@studio.ie")
    ).scalar_one()
    subject = session.execute(select(Client)).scalars().first()

    artists = {}
    for handle in {row[1] for row in ROWS}:
        artists[handle] = session.execute(
            select(UserAccount).where(UserAccount.email == f"{handle}@studio.ie")
        ).scalar_one()

    existing = session.execute(
        select(TattooSession).where(TattooSession.description_hint == "OUT26")
    ).first() if hasattr(TattooSession, "description_hint") else None

    created = 0
    for day, handle, charged, percentage in ROWS:
        when = datetime(2026, 10, day, 14, tzinfo=DUBLIN)
        quote = Quote(
            client_id=subject.id,
            artist_id=artists[handle].id,
            created_by=owner.id,
            origin=QuoteOrigin.ARTIST_OWN,
            description=f"October control {day:02d} {handle}",
            body_region="Forearm",
            size_estimate="15cm",
            total_value=Decimal(charged),
            planned_sessions=1,
            planned_value_per_session=Decimal(charged),
            estimated_duration_minutes=120,
            status=QuoteStatus.APPROVED,
            artist_percentage=Decimal(percentage),
            approved_at=when,
            approved_by=owner.id,
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
                marked_done_by=artists[handle].id,
                confirmed_at=when,
                confirmed_by=owner.id,
            )
        )
        created += 1
    session.commit()
    print(f"{created} atendimentos de outubro lancados")
