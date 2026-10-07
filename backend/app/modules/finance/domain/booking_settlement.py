from app.modules.finance.domain.settlement_event import SettlementEvent
from app.modules.finance.domain.settlement_outcome import SettlementOutcome


class BookingSettlement:
    """O destino do dinheiro em cada desfecho do agendamento.

    É a letra das regras num mapa só, e não espalhada por quem cancela, quem
    recusa e quem remarca. As quatro tratam o sinal de forma diferente, e a
    diferença é justamente o que se perde quando cada caso de uso decide
    sozinho:

    | Desfecho | Sinal | Acima do sinal | Regra |
    |---|---|---|---|
    | Estúdio recusou | devolvido | devolvido | RN-PAG-003 |
    | Cancelado sem nova data | retido, mesmo com aviso de 24h | devolvido | RN-AGE-009 |
    | Não compareceu | retido | devolvido | RN-AGE-010, RN-PAG-004 |
    | Remarcado com 24h | segue para o novo horário | segue junto | RN-AGE-008 |
    | Remarcado fora do prazo | perdido pelo cliente | devolvido | RN-AGE-008 |

    **Retido não é devolvido, e a diferença importa.** O estúdio ficou com o
    dinheiro para compensar o horário reservado e a preparação do desenho
    (RN-AGE-009). O pagamento continua confirmado no histórico; o que ele deixa
    de fazer é valer como sinal daquele horário.

    Decisão pura: não conhece pagamento, banco nem ator."""

    _BY_EVENT: dict[SettlementEvent, SettlementOutcome] = {
        SettlementEvent.REJECTED_BY_STUDIO: SettlementOutcome(
            refund_deposit=True, retain_deposit=False, refund_above_deposit=True
        ),
        SettlementEvent.CANCELLED: SettlementOutcome(
            refund_deposit=False, retain_deposit=True, refund_above_deposit=True
        ),
        SettlementEvent.NO_SHOW: SettlementOutcome(
            refund_deposit=False, retain_deposit=True, refund_above_deposit=True
        ),
        SettlementEvent.RESCHEDULED_IN_TIME: SettlementOutcome(
            refund_deposit=False, retain_deposit=False, refund_above_deposit=False
        ),
        SettlementEvent.RESCHEDULED_LATE: SettlementOutcome(
            refund_deposit=False, retain_deposit=True, refund_above_deposit=True
        ),
    }

    _REASON: dict[SettlementEvent, str] = {
        SettlementEvent.REJECTED_BY_STUDIO: "The studio rejected the request.",
        SettlementEvent.CANCELLED: "The booking was cancelled without a new date.",
        SettlementEvent.NO_SHOW: "The client did not show up.",
        SettlementEvent.RESCHEDULED_IN_TIME: "The booking moved within the 24-hour notice.",
        SettlementEvent.RESCHEDULED_LATE: "The booking moved outside the 24-hour notice.",
    }

    def decide(self, event: SettlementEvent) -> SettlementOutcome:
        return BookingSettlement._BY_EVENT[event]

    def reason(self, event: SettlementEvent) -> str:
        """O motivo que acompanha a devolução e a retenção no histórico. Vem
        daqui para que a mesma frase não seja reescrita em cada caso de uso —
        e as regras exigem motivo registrado em ambos (RN-PAG-007, RN-PAG-009)."""
        return BookingSettlement._REASON[event]
