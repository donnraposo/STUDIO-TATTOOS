"""A semana de repasse e a divisao por sessao (RN-REP-004 e RN-REP-007).

O risco declarado da M6 e a fronteira do horario de verao. O erro seria de uma
hora na borda da sexta-feira, pegando justamente os pagamentos confirmados entre
19h e 21h -- e um repasse que inclui ou exclui uma sessao por engano so e
descoberto quando o artista confere o proprio extrato.

Sem banco: sao decisoes puras, e e nelas que esse erro mora.
"""

from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.modules.finance.domain.payout_share import PayoutShare
from app.modules.finance.domain.payout_week import PayoutWeek

DUBLIN = ZoneInfo("Europe/Dublin")


def _dublin(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=DUBLIN)


class TestPayoutWeek:
    def test_a_saturday_belongs_to_the_friday_ahead(self) -> None:
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 10, 3, 11))

        assert closing.astimezone(DUBLIN) == _dublin(2026, 10, 9, 20)

    def test_a_friday_morning_belongs_to_that_same_friday(self) -> None:
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 10, 9, 10))

        assert closing.astimezone(DUBLIN) == _dublin(2026, 10, 9, 20)

    def test_eight_pm_sharp_closes_the_week_it_ends(self) -> None:
        """RN-REP-004: "pagamentos recebidos na propria sexta-feira entrarao no
        repasse daquele dia". O intervalo e fechado no fim, senao o pagamento das
        20h em ponto cairia em nenhuma das duas semanas."""
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 10, 9, 20))

        assert closing.astimezone(DUBLIN) == _dublin(2026, 10, 9, 20)

    def test_a_minute_past_eight_goes_to_the_next_week(self) -> None:
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 10, 9, 20, 1))

        assert closing.astimezone(DUBLIN) == _dublin(2026, 10, 16, 20)

    def test_the_closing_is_eight_pm_in_dublin_in_summer(self) -> None:
        """Julho: Dublin esta em UTC+1, entao 20h locais sao 19h UTC. Calcular em
        UTC daria 20h UTC, uma hora depois."""
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 7, 10, 10))

        assert closing == datetime(2026, 7, 10, 19, tzinfo=UTC)

    def test_the_closing_is_eight_pm_in_dublin_in_winter(self) -> None:
        """Janeiro: Dublin esta em UTC, e 20h locais sao 20h UTC. O mesmo codigo
        tem de dar as duas respostas, que e o ponto."""
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 1, 9, 10))

        assert closing == datetime(2026, 1, 9, 20, tzinfo=UTC)

    def test_the_week_that_crosses_daylight_saving_is_not_seven_times_24h(self) -> None:
        """O horario de verao irlandes termina no ultimo domingo de outubro: 25
        de outubro de 2026. A semana que o atravessa tem 169 horas, nao 168.

        Subtrair sete dias em UTC daria 168 e deixaria uma hora de fora -- e
        nela caberia um pagamento confirmado no sabado de madrugada."""
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 10, 30, 10))
        opening = week.opening_for(closing)

        assert closing.astimezone(DUBLIN) == _dublin(2026, 10, 30, 20)
        assert opening.astimezone(DUBLIN) == _dublin(2026, 10, 23, 20)
        assert (closing - opening).total_seconds() / 3600 == 169

    def test_an_ordinary_week_is_seven_times_24h(self) -> None:
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 7, 10, 10))

        assert (closing - week.opening_for(closing)).total_seconds() / 3600 == 168

    def test_the_opening_is_the_previous_closing(self) -> None:
        """Semanas consecutivas se encostam sem buraco nem sobreposicao."""
        week = PayoutWeek()

        closing = week.closing_for(_dublin(2026, 10, 9, 10))
        opening = week.opening_for(closing)

        assert opening == week.closing_for(_dublin(2026, 10, 2, 19))


class TestPayoutShare:
    def test_seventy_percent_of_a_round_amount(self) -> None:
        assert PayoutShare().of(Decimal("250.00"), Decimal("70.00")) == Decimal("175.00")

    def test_fifty_percent_of_a_round_amount(self) -> None:
        assert PayoutShare().of(Decimal("250.00"), Decimal("50.00")) == Decimal("125.00")

    def test_the_example_from_the_business_rules(self) -> None:
        """RN-PAG-005: tatuagem de EUR 100 para cliente proprio paga EUR 70 ao
        artista e deixa EUR 30 ao estudio."""
        assert PayoutShare().of(Decimal("100.00"), Decimal("70.00")) == Decimal("70.00")

    def test_half_a_cent_rounds_up(self) -> None:
        """`ROUND_HALF_UP` e nao o padrao do Python. O arredondamento bancario
        daria EUR 0,12 aqui, e ninguem quer explicar ao artista por que meio
        centavo some numa semana e aparece na outra."""
        assert PayoutShare().of(Decimal("0.25"), Decimal("50.00")) == Decimal("0.13")

    def test_each_session_is_rounded_on_its_own(self) -> None:
        """RN-REP-007: "calculado separadamente para cada sessao e arredondado
        para duas casas". Somar primeiro e arredondar no fim da outro numero.

        Tres sessoes de EUR 33,33 a 70%: cada uma da EUR 23,33 e somam EUR 69,99.
        Somando antes seriam EUR 99,99 a 70%, isto e, EUR 69,99 tambem -- mas com
        EUR 33,35 a divergencia aparece, e e por isso que a ordem tem teste."""
        share = PayoutShare()
        separately = sum(
            (share.of(Decimal("33.35"), Decimal("70.00")) for _ in range(3)), Decimal("0")
        )

        assert separately == Decimal("70.05")
        assert share.of(Decimal("100.05"), Decimal("70.00")) == Decimal("70.04")
