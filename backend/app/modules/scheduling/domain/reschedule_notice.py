from datetime import datetime, timedelta

from app.modules.scheduling.domain.booking_outcome import BookingOutcome


class RescheduleNotice:
    """A regra das 24 horas da remarcação (RN-AGE-008).

    Dentro do prazo o sinal e os demais valores acompanham o novo horário; fora
    dele o cliente perde o sinal e precisa pagar um novo, e o que pagou acima do
    sinal é devolvido.

    **O prazo conta a partir do horário marcado, não da data da criação.** Avisar
    com 24 horas de antecedência é avisar 24 horas antes de o cliente ser
    atendido — contar do dia em que o horário foi pedido daria mais prazo a quem
    marcou com meses de antecedência, que é o contrário do que a regra protege:
    o horário reservado e a preparação do desenho.

    Decisão pura, com o instante recebido de fora. Ler o relógio aqui dentro
    tornaria a classe impossível de testar sem esperar o tempo passar."""

    NOTICE = timedelta(hours=24)

    def outcome(self, original_start: datetime, requested_at: datetime) -> BookingOutcome:
        within = original_start - requested_at >= RescheduleNotice.NOTICE
        return (
            BookingOutcome.RESCHEDULED_IN_TIME if within else BookingOutcome.RESCHEDULED_LATE
        )
