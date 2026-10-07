from datetime import UTC, datetime
from zoneinfo import ZoneInfo


class RevenueMonth:
    """Os limites de um mês no fuso do estúdio (RN 10.4).

    **O mês é um intervalo de instantes, não um intervalo de datas.** Outubro
    começa à meia-noite de Dublin do dia 1º, e esse instante é 23h de 30 de
    setembro em UTC no horário de verão irlandês, e meia-noite em UTC no
    inverno. Calcular em UTC e torcer daria um mês certo em janeiro e errado em
    julho — e o erro seria de uma hora na borda, pegando justamente o
    atendimento confirmado no fim da última noite do mês.

    É o mesmo cuidado do `PayoutWeek`, pela mesma razão.

    **Aberto no começo e fechado no fim não se aplica aqui**: o mês é
    meio-aberto — `[primeiro instante, primeiro instante do mês seguinte)`. Um
    atendimento confirmado à meia-noite em ponto do dia 1º pertence ao mês que
    começa, e não ao que termina; sem essa escolha ele cairia nos dois.

    Classe pura: recebe o mês, não lê o relógio. Ler a hora aqui tornaria o
    cálculo impossível de testar sem esperar o mês virar."""

    TIME_ZONE = ZoneInfo("Europe/Dublin")

    def bounds_for(self, year: int, month: int) -> tuple[datetime, datetime]:
        """O primeiro instante do mês e o primeiro do mês seguinte, em UTC."""
        start = datetime(year, month, 1, tzinfo=RevenueMonth.TIME_ZONE)
        end = datetime(*self.next_month(year, month), 1, tzinfo=RevenueMonth.TIME_ZONE)
        return start.astimezone(UTC), end.astimezone(UTC)

    def next_month(self, year: int, month: int) -> tuple[int, int]:
        return (year + 1, 1) if month == 12 else (year, month + 1)

    def previous_month(self, year: int, month: int) -> tuple[int, int]:
        return (year - 1, 12) if month == 1 else (year, month - 1)

    def recent(self, year: int, month: int, count: int) -> list[tuple[int, int]]:
        """Os `count` meses que terminam neste, do mais antigo para o mais novo.

        A ordem é a da leitura: a comparação entre meses só diz alguma coisa
        quando o tempo corre da esquerda para a direita."""
        months: list[tuple[int, int]] = []
        cursor = (year, month)
        for _ in range(max(count, 1)):
            months.append(cursor)
            cursor = self.previous_month(*cursor)
        return list(reversed(months))
