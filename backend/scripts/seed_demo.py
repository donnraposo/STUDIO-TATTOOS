"""Dados de demonstracao para a fatia de interface (M7.1.1).

Roda dentro do container:

    docker compose exec api sh -c 'cd /app &&
      PYTHONPATH=/app SEED_DEMO_PASSWORD=<senha> python scripts/seed_demo.py'

As duas variaveis sao necessarias e nao vem do ambiente do container: sem
`PYTHONPATH` o import de `app` falha, porque `python scripts/...` poe
`/app/scripts` no caminho e nao `/app`; `SEED_DEMO_PASSWORD` nao esta no
`docker-compose.yml` de proposito, para que a senha de demonstracao exista
apenas no comando de quem a roda.

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
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from psycopg.types.range import Range
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
from app.modules.scheduling.domain.booking_status import BookingStatus
from app.modules.scheduling.infrastructure.models.bench import Bench
from app.modules.scheduling.infrastructure.models.booking import Booking


class DemoSeeder:
    """Popula o banco com o minimo para a interface ter o que mostrar.

    Quatro macas, as contas de gestao e a equipe de artistas do estudio. Os
    clientes ficam ligados a artistas diferentes de proposito, porque e isso que
    torna visivel na tela a regra de visibilidade da RN-CLI-004 -- um residente
    nao pode ver a ficha completa do cliente do outro.
    """

    # A equipe real do estudio, pelos nomes que ele usa. Duas coisas ficam
    # **em branco de proposito**, e as duas sao decisao do estudio, tomada na
    # tela de contas:
    #
    # - **Perfil.** Todos entram como residente, que e o perfil corrente de
    #   artista. Quem e guest varia por temporada, e nada na documentacao diz
    #   quem e o que -- chutar aqui colocaria alguem fora da exigencia de sinal
    #   da RN-GST-004 por invencao do seed.
    # - **Percentual.** Nulo, ou seja, regra da origem: 70% no cliente proprio
    #   e 50% na indicacao. A planilha do estudio mostra acordos de 85%, mas
    #   nao ha como saber de quem sem perguntar, e escrever o acordo errado de
    #   alguem e pior do que nao escrever nenhum.
    #
    # O nome vai nos dois campos porque a lista enviada pelo estudio traz o
    # nome pelo qual ele chama cada pessoa, e **artista sem nome de artista o
    # banco recusa** (ck_user_account_artist_name_required). Onde o nome civil
    # difere, o estudio corrige na tela de contas.
    #
    # As duas contas de gestao e a conta guest sao ficticias, e existem para a
    # demonstracao ter quem decide e quem cai na RN-GST-004.
    _ACCOUNTS = [
        ("owner@studio.ie", "Aoife Byrne", UserRole.OWNER, True, "Nyx"),
        ("manager@studio.ie", "Cillian Walsh", UserRole.MANAGER, False, None),
        ("ytalo@studio.ie", "Ytalo Lyra", UserRole.RESIDENT, False, "Ytalo Lyra"),
        ("lisa@studio.ie", "Lisa", UserRole.RESIDENT, False, "Lisa"),
        ("bohdan@studio.ie", "Bohdan", UserRole.RESIDENT, False, "Bohdan"),
        ("warlen@studio.ie", "Warlen", UserRole.RESIDENT, False, "Warlen"),
        ("jay@studio.ie", "Jay", UserRole.RESIDENT, False, "Jay"),
        ("duda@studio.ie", "Duda", UserRole.RESIDENT, False, "Duda"),
        ("lipo@studio.ie", "Lipo", UserRole.RESIDENT, False, "Lipo"),
        ("farpa@studio.ie", "Farpa", UserRole.RESIDENT, False, "Farpa"),
        ("yukimy@studio.ie", "Yukimy Midory", UserRole.RESIDENT, False, "Yukimy Midory"),
        ("guest@studio.ie", "Lucia Ferrari", UserRole.GUEST, False, "Lu"),
    ]

    # Quatro macas, identificadas apenas pelo numero (RN-AGE-001). Sem apelido:
    # nenhuma regra pede, e nome inventado aqui vira nome inventado na operacao.
    _BENCHS = [1, 2, 3, 4]

    _CLIENTS = [
        ("Niamh O'Sullivan", "+353 87 111 1111", "@niamh.os", "ytalo@studio.ie"),
        ("Declan Moore", "+353 86 222 2222", None, "ytalo@studio.ie"),
        ("Roisin Doyle", "+353 85 333 3333", "@roisin.d", "lisa@studio.ie"),
    ]

    def __init__(self, session: Session, password: str) -> None:
        self._session = session
        self._password = password
        self._hasher = PasswordHasher()

    # Agenda de hoje: hora de inicio, duracao, indice da maca, artista e estado.
    # Artistas e macas diferentes de proposito, para nao esbarrar nas restricoes
    # EXCLUDE -- que e justamente o que a demonstracao quer mostrar funcionando.
    _BOOKINGS = [
        (10, 2, 0, "ytalo@studio.ie", BookingStatus.APPROVED),
        (13, 3, 1, "lisa@studio.ie", BookingStatus.APPROVED),
        (15, 2, 0, "guest@studio.ie", BookingStatus.REQUESTED),
        (17, 2, 2, "owner@studio.ie", BookingStatus.APPROVED),
    ]

    def run(self) -> None:
        accounts = self._seed_accounts()
        benches = self._seed_benches()
        clients = self._seed_clients(accounts)
        self._seed_quote(accounts, clients)
        self._seed_bookings(accounts, benches, clients)
        self._session.commit()

    def _seed_bookings(
        self,
        accounts: dict[str, UserAccount],
        benches: list[Bench],
        clients: list[Client],
    ) -> None:
        """Agenda do dia corrente, para a timeline abrir com conteudo.

        Usa HOJE e nao uma data fixa: uma agenda semeada em setembro estaria
        vazia em outubro, e quem abrisse a tela concluiria que ela nao
        funciona."""
        if self._session.execute(select(Booking)).first() is not None:
            return

        today = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        for hour, duration, bench_index, artist_email, status in self._BOOKINGS:
            start = today.replace(hour=hour)
            self._session.add(
                Booking(
                    client_id=clients[bench_index % len(clients)].id,
                    artist_id=accounts[artist_email].id,
                    bench_id=benches[bench_index].id,
                    period=Range(start, start + timedelta(hours=duration), bounds="[)"),
                    status=status,
                    decided_at=today if status == BookingStatus.APPROVED else None,
                    decided_by=accounts["owner@studio.ie"].id
                    if status == BookingStatus.APPROVED
                    else None,
                )
            )
        self._session.flush()

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

    def _seed_benches(self) -> list[Bench]:
        for number in self._BENCHS:
            existing = self._session.execute(
                select(Bench).where(Bench.number == number)
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(Bench(number=number))
        self._session.flush()
        return list(self._session.execute(select(Bench).order_by(Bench.number)).scalars())

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
                artist_id=accounts["ytalo@studio.ie"].id,
                created_by=accounts["ytalo@studio.ie"].id,
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
