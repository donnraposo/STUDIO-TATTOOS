"""Os limites do mes e a divisao do faturamento (RN 10.4 e RN-REP-007).

O risco aqui e o mesmo da semana de repasse, por outra borda: o mes comeca a
meia-noite de Dublin, e esse instante muda de hora em UTC duas vezes por ano. O
erro seria de uma hora na virada do mes, pegando justamente o atendimento
confirmado no fim da ultima noite -- e so apareceria quando alguem comparasse o
relatorio com a planilha e achasse uma linha a mais ou a menos.

Sem banco: sao decisoes puras, e e nelas que esse erro mora.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.modules.finance.domain.payout_share import PayoutShare
from app.modules.finance.domain.revenue_ledger import RevenueLedger
from app.modules.finance.domain.revenue_month import RevenueMonth
from app.modules.finance.domain.settled_session import SettledSession

DUBLIN = ZoneInfo("Europe/Dublin")


def _settled(charged: str, percentage: str) -> SettledSession:
    return SettledSession(
        session_id=uuid.uuid4(),
        artist_id=uuid.uuid4(),
        received_amount=Decimal(charged),
        percentage=Decimal(percentage),
        confirmed_at=datetime(2026, 10, 1, 14, tzinfo=DUBLIN),
    )


class TestRevenueMonth:
    def test_october_starts_at_midnight_in_dublin_not_in_utc(self) -> None:
        """Outubro de 2026 comeca no horario de verao irlandes, UTC+1: a
        meia-noite de Dublin e 23h de 30 de setembro em UTC. Calcular em UTC
        daria uma hora a mais no comeco, e o atendimento das 23h30 do dia 30
        entraria em outubro."""
        start, _ = RevenueMonth().bounds_for(2026, 10)

        assert start == datetime(2026, 9, 30, 23, tzinfo=UTC)

    def test_january_starts_at_midnight_utc(self) -> None:
        """Em janeiro Dublin esta em UTC. O mesmo codigo tem de dar as duas
        respostas, que e o ponto."""
        start, _ = RevenueMonth().bounds_for(2026, 1)

        assert start == datetime(2026, 1, 1, 0, tzinfo=UTC)

    def test_the_month_ends_where_the_next_one_begins(self) -> None:
        """Meio-aberto: um atendimento confirmado a meia-noite em ponto do dia
        1o pertence ao mes que comeca. Sem essa escolha ele cairia nos dois."""
        months = RevenueMonth()

        _, october_end = months.bounds_for(2026, 10)
        november_start, _ = months.bounds_for(2026, 11)

        assert october_end == november_start

    def test_december_rolls_into_the_next_year(self) -> None:
        _, end = RevenueMonth().bounds_for(2026, 12)

        assert end.astimezone(DUBLIN) == datetime(2027, 1, 1, tzinfo=DUBLIN)

    def test_the_month_that_loses_an_hour_still_starts_at_midnight(self) -> None:
        """Marco de 2026: o horario de verao entra no dia 29, dentro do mes. O
        comeco do mes nao muda, mas o fim dele sim -- e e por isso que os dois
        limites sao calculados no fuso, e nao somando dias a um deles."""
        start, end = RevenueMonth().bounds_for(2026, 3)

        assert start == datetime(2026, 3, 1, 0, tzinfo=UTC)
        assert end == datetime(2026, 3, 31, 23, tzinfo=UTC)

    def test_recent_months_run_forwards_in_time(self) -> None:
        """A comparacao entre meses so diz alguma coisa quando o tempo corre da
        esquerda para a direita."""
        assert RevenueMonth().recent(2026, 2, 4) == [
            (2025, 11),
            (2025, 12),
            (2026, 1),
            (2026, 2),
        ]

    def test_asking_for_one_month_gives_that_month(self) -> None:
        assert RevenueMonth().recent(2026, 10, 1) == [(2026, 10)]


class TestRevenueLedger:
    def test_the_two_shares_add_up_to_what_the_client_paid(self) -> None:
        """A conferencia que o estudio faz na planilha, e que tem de valer em
        qualquer valor. A parte da casa e o resto, e nao uma segunda
        multiplicacao: calculadas em separado, as duas falhariam a soma por um
        centavo sempre que o arredondamento subisse."""
        ledger = RevenueLedger(PayoutShare())

        for charged in ["0.01", "33.33", "99.99", "250.00", "1000.01"]:
            line = ledger.lines([_settled(charged, "70.00")], set())[0]

            assert line.artist_amount + line.studio_amount == Decimal(charged)

    def test_the_split_matches_the_one_the_artist_is_paid(self) -> None:
        """Usa o mesmo `PayoutShare` do repasse de proposito. Com um calculo
        proprio, o estudio teria dois numeros para a mesma coisa: o que o painel
        mostra e o que o artista recebe."""
        share = PayoutShare()
        line = RevenueLedger(share).lines([_settled("130.00", "85.00")], set())[0]

        assert line.artist_amount == share.of(Decimal("130.00"), Decimal("85.00"))
        assert line.artist_amount == Decimal("110.50")

    def test_the_deposit_does_not_come_off_the_value(self) -> None:
        """RN-PAG-005: "o sinal integrara o preco da tatuagem e a base de
        calculo do repasse". O valor cobrado ja o contem, e subtrai-lo aqui
        pagaria o artista a menos."""
        line = RevenueLedger(PayoutShare()).lines([_settled("250.00", "85.00")], set())[0]

        assert line.value == Decimal("250.00")
        assert line.artist_amount == Decimal("212.50")

    def test_totals_sum_lines_already_rounded(self) -> None:
        """RN-REP-007 manda arredondar por sessao. Somar primeiro e arredondar
        no fim daria um total que nao confere com nenhuma das linhas que o
        explicam."""
        ledger = RevenueLedger(PayoutShare())
        sessions = [_settled("33.33", "70.00"), _settled("33.33", "70.00")]

        totals = ledger.totals(ledger.lines(sessions, set()))

        assert totals.artists == Decimal("23.33") * 2
        assert totals.sessions == 2

    def test_nothing_settled_gives_zero_and_not_an_empty_answer(self) -> None:
        totals = RevenueLedger(PayoutShare()).totals([])

        assert totals.sessions == 0
        assert totals.value == Decimal("0.00")
        assert totals.studio == Decimal("0.00")

    def test_a_session_already_transferred_is_marked_as_such(self) -> None:
        ledger = RevenueLedger(PayoutShare())
        settled = _settled("100.00", "70.00")

        paid = ledger.lines([settled], {settled.session_id})[0]
        unpaid = ledger.lines([settled], set())[0]

        assert paid.transferred is True
        assert unpaid.transferred is False
