"""Dados de demonstracao para a fatia de interface (M7.1.1).

Roda dentro do container:

    docker compose exec api python scripts/seed_demo.py

**So executa em desenvolvimento.** Cria contas com senha conhecida; rodar isto
em producao seria abrir o sistema para quem souber ler o `.env.example`. A
recusa e por `ENVIRONMENT`, conferida antes de qualquer escrita.

A senha vem de `SEED_DEMO_PASSWORD`, com o valor de desenvolvimento registrado
no `.env.example` -- mesmo padrao das demais credenciais locais do projeto. Nao
fica escrita aqui para que trocar o valor nao exija tocar em codigo.

E idempotente: rodar duas vezes nao duplica nada. Sem isso, a segunda execucao
esbarraria na unicidade do e-mail e deixaria o banco pela metade.
"""

import os
import sys
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.container import Container
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.password_hasher import PasswordHasher
from app.modules.quotes.domain.quote_origin import QuoteOrigin
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.scheduling.infrastructure.models.booth import Booth


class DemoSeeder:
    """Popula o banco com o minimo para a interface ter o que mostrar.

    O conteudo segue a configuracao operacional aprovada: quatro macas, um
    proprietario, um gerente, dois residentes e um guest. Os clientes ficam
    ligados a residentes diferentes de proposito, porque e isso que torna
    visivel na tela a regra de visibilidade da RN-CLI-004 -- um residente nao
    pode ver a ficha completa do cliente do outro.
    """

    _ACCOUNTS = [
        ("owner@studio.ie", "Aoife Byrne", UserRole.OWNER, True, "Nyx"),
        ("manager@studio.ie", "Cillian Walsh", UserRole.MANAGER, False, None),
        ("resident@studio.ie", "Saoirse Kelly", UserRole.RESIDENT, False, "Vera"),
        ("resident2@studio.ie", "Eoin Murphy", UserRole.RESIDENT, False, "Corvo"),
        ("guest@studio.ie", "Lucia Ferrari", UserRole.GUEST, False, "Lu"),
    ]

    _BOOTHS = [(1, "Window"), (2, "Back"), (3, "Studio"), (4, "Private")]

    _CLIENTS = [
        ("Niamh O'Sullivan", "+353 87 111 1111", "@niamh.os", "resident@studio.ie"),
        ("Declan Moore", "+353 86 222 2222", None, "resident@studio.ie"),
        ("Roisin Doyle", "+353 85 333 3333", "@roisin.d", "resident2@studio.ie"),
    ]

    def __init__(self, session: Session, password: str) -> None:
        self._session = session
        self._password = password
        self._hasher = PasswordHasher()

    def run(self) -> None:
        accounts = self._seed_accounts()
        self._seed_booths()
        clients = self._seed_clients(accounts)
        self._seed_quote(accounts, clients)
        self._session.commit()

    def _seed_accounts(self) -> dict[str, UserAccount]:
        created: dict[str, UserAccount] = {}
        for email, full_name, role, acts_as_artist, artist_name in self._ACCOUNTS:
            existing = self._session.execute(
                select(UserAccount).where(UserAccount.email == email)
            ).scalar_one_or_none()
            if existing is not None:
                created[email] = existing
                continue

            account = UserAccount(
                email=email,
                password_hash=self._hasher.hash(self._password),
                full_name=full_name,
                artist_name=artist_name,
                phone="+353 21 000 0000",
                role=role,
                acts_as_artist=acts_as_artist,
                status=UserStatus.ACTIVE,
            )
            self._session.add(account)
            created[email] = account

        self._session.flush()
        return created

    def _seed_booths(self) -> None:
        for number, label in self._BOOTHS:
            existing = self._session.execute(
                select(Booth).where(Booth.number == number)
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(Booth(number=number, label=label))
        self._session.flush()

    def _seed_clients(self, accounts: dict[str, UserAccount]) -> list[Client]:
        clients: list[Client] = []
        for name, phone, instagram, artist_email in self._CLIENTS:
            existing = self._session.execute(
                select(Client).where(Client.phone == phone)
            ).scalar_one_or_none()
            if existing is not None:
                clients.append(existing)
                continue

            client = Client(
                name=name,
                phone=phone,
                instagram=instagram,
                registered_by_artist_id=accounts[artist_email].id,
            )
            self._session.add(client)
            clients.append(client)

        self._session.flush()
        return clients

    def _seed_quote(self, accounts: dict[str, UserAccount], clients: list[Client]) -> None:
        """Um orcamento pendente, para a tela ter o que decidir.

        Pendente e nao aprovado de proposito: aprovado, ele ja chegaria com o
        percentual congelado e a demonstracao perderia justamente o momento em
        que a RN-REP-006 acontece."""
        if self._session.execute(select(Quote)).first() is not None:
            return

        self._session.add(
            Quote(
                client_id=clients[0].id,
                artist_id=accounts["resident@studio.ie"].id,
                created_by=accounts["resident@studio.ie"].id,
                origin=QuoteOrigin.ARTIST_OWN,
                description="Blackwork forearm sleeve, botanical motifs",
                body_region="Left forearm",
                size_estimate="20cm",
                total_value=Decimal("1000.00"),
                planned_sessions=4,
                planned_value_per_session=Decimal("250.00"),
                estimated_duration_minutes=180,
                status=QuoteStatus.PENDING,
            )
        )
        self._session.flush()


if __name__ == "__main__":
    container = Container()

    if container.settings.environment.lower() != "development":
        print("Recusado: seed_demo so roda com ENVIRONMENT=development.", file=sys.stderr)
        raise SystemExit(1)

    demo_password = os.environ.get("SEED_DEMO_PASSWORD")
    if not demo_password:
        print("Recusado: defina SEED_DEMO_PASSWORD (ver .env.example).", file=sys.stderr)
        raise SystemExit(1)

    with container.database.session() as database_session:
        DemoSeeder(database_session, demo_password).run()

    print("Dados de demonstracao prontos. Contas em backend/scripts/seed_demo.py.")
