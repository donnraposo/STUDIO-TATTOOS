from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


class PayoutWeek:
    """A semana de repasse: de sexta 20h a sexta 20h, no fuso do estúdio
    (RN-REP-004).

    **O fechamento é um instante, não uma data.** A regra diz "20h de
    sexta-feira, no fuso `Europe/Dublin`", e esse instante muda de hora em UTC
    duas vezes por ano, quando o horário de verão irlandês entra e sai. Calcular
    em UTC e torcer daria uma semana certa em março e errada em abril — e o erro
    seria de uma hora na borda, pegando justamente os pagamentos confirmados
    entre 19h e 21h da sexta.

    **Pagamento recebido na própria sexta entra no repasse daquele dia**, diz a
    regra. Por isso o intervalo é fechado no fim: o que aconteceu exatamente às
    20h de sexta pertence à semana que fecha, e não à seguinte. Sem essa escolha
    explícita, um pagamento confirmado às 20h em ponto cairia em nenhuma das
    duas, ou nas duas.

    Classe pura: recebe o instante de referência, não lê o relógio. Ler a hora
    aqui dentro tornaria o cálculo impossível de testar sem esperar sexta-feira
    chegar."""

    TIME_ZONE = ZoneInfo("Europe/Dublin")
    CLOSING_HOUR = 20
    FRIDAY = 4

    def closing_for(self, moment: datetime) -> datetime:
        """A primeira sexta às 20h do estúdio **igual ou posterior** ao instante
        dado, em UTC.

        Um pagamento de sábado pertence à sexta seguinte; um de sexta às 19h, à
        sexta do mesmo dia; um de sexta às 20h em ponto, àquela mesma."""
        local = moment.astimezone(PayoutWeek.TIME_ZONE)
        friday = local.date() + timedelta(days=(PayoutWeek.FRIDAY - local.weekday()) % 7)

        closing = self._at_closing(friday)
        if local > closing:
            closing = self._at_closing(friday + timedelta(days=7))
        return closing.astimezone(UTC)

    def opening_for(self, closing: datetime) -> datetime:
        """A abertura é o fechamento da semana anterior.

        Calculada no fuso do estúdio e não subtraindo sete dias em UTC: na semana
        em que o horário de verão vira, os dois resultados diferem de uma hora, e
        o intervalo deixaria um buraco ou uma sobreposição."""
        previous = closing.astimezone(PayoutWeek.TIME_ZONE).date() - timedelta(days=7)
        return self._at_closing(previous).astimezone(UTC)

    def _at_closing(self, day: date) -> datetime:
        """As 20h do estúdio naquele dia.

        Montado a partir dos componentes da data para que o deslocamento seja o
        vigente **naquele dia**, e não o do instante que originou a pergunta."""
        return datetime(
            day.year,
            day.month,
            day.day,
            PayoutWeek.CLOSING_HOUR,
            tzinfo=PayoutWeek.TIME_ZONE,
        )
