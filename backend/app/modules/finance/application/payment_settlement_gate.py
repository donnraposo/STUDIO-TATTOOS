import uuid

from app.modules.finance.application.settle_booking import SettleBooking
from app.modules.finance.domain.settlement_event import SettlementEvent
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.scheduling.domain.booking_outcome import BookingOutcome
from app.modules.scheduling.domain.booking_settlement_gate import BookingSettlementGate


class PaymentSettlementGate(BookingSettlementGate):
    """Traduz o desfecho da agenda em evento financeiro.

    É a peça que liga os dois vocabulários, e existe para que nenhum dos dois
    módulos precise aprender o do outro. A tradução é um mapa de dados: um
    desfecho novo na agenda é uma linha aqui, não uma condicional nova dentro do
    financeiro.

    A agenda diz "recusado"; o financeiro entende "o estúdio recusou, devolve o
    sinal integralmente" (RN-PAG-003). São a mesma coisa vista de dois lados, e
    é exatamente por isso que a traducao mora na fronteira."""

    _EVENT_BY_OUTCOME: dict[BookingOutcome, SettlementEvent] = {
        BookingOutcome.REJECTED: SettlementEvent.REJECTED_BY_STUDIO,
        BookingOutcome.CANCELLED: SettlementEvent.CANCELLED,
        BookingOutcome.NO_SHOW: SettlementEvent.NO_SHOW,
        BookingOutcome.RESCHEDULED_IN_TIME: SettlementEvent.RESCHEDULED_IN_TIME,
        BookingOutcome.RESCHEDULED_LATE: SettlementEvent.RESCHEDULED_LATE,
    }

    def __init__(self, settle: SettleBooking) -> None:
        self._settle = settle

    def settle(
        self, actor: AuthenticatedUser, booking_id: uuid.UUID, outcome: BookingOutcome
    ) -> None:
        self._settle.execute(
            actor, booking_id, PaymentSettlementGate._EVENT_BY_OUTCOME[outcome]
        )
