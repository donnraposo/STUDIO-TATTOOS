"""Decisoes puras do financeiro (RN-PAG-001, RN-PAG-007, RN-AGE-008, RN-AGE-009,
RN-AGE-010, RN-PAG-003 e RN-GST-004).

Sem banco: sao as regras que erram em silencio. Um estado que aceita voltar
atras apaga uma recusa do historico; um desfecho que devolve o sinal onde a
regra manda reter tira dinheiro do caixa sem que ninguem perceba ate o
fechamento.
"""

from datetime import UTC, datetime, timedelta

from app.modules.finance.domain.booking_settlement import BookingSettlement
from app.modules.finance.domain.deposit_policy import DepositPolicy
from app.modules.finance.domain.payment_status import PaymentStatus
from app.modules.finance.domain.payment_transition import PaymentTransition
from app.modules.finance.domain.settlement_event import SettlementEvent
from app.modules.identity.domain.user_role import UserRole
from app.modules.scheduling.domain.booking_outcome import BookingOutcome
from app.modules.scheduling.domain.reschedule_notice import RescheduleNotice

APPOINTMENT = datetime(2026, 10, 10, 14, 0, tzinfo=UTC)


class TestPaymentTransition:
    """RN-PAG-007: `Informado → Confirmado ou Recusado → Devolvido ou Estornado`."""

    def test_reported_goes_to_confirmed_or_refused(self) -> None:
        transitions = PaymentTransition()

        assert transitions.allows(PaymentStatus.REPORTED, PaymentStatus.CONFIRMED)
        assert transitions.allows(PaymentStatus.REPORTED, PaymentStatus.REFUSED)

    def test_confirmed_goes_to_refunded_or_charged_back(self) -> None:
        transitions = PaymentTransition()

        assert transitions.allows(PaymentStatus.CONFIRMED, PaymentStatus.REFUNDED)
        assert transitions.allows(PaymentStatus.CONFIRMED, PaymentStatus.CHARGED_BACK)

    def test_a_refused_payment_never_becomes_confirmed(self) -> None:
        """Voltar atras apagaria a recusa do historico, e a regra manda corrigir
        por lancamento novo, nao por reescrita."""
        assert not PaymentTransition().allows(PaymentStatus.REFUSED, PaymentStatus.CONFIRMED)

    def test_refunded_and_charged_back_are_final(self) -> None:
        transitions = PaymentTransition()

        assert transitions.is_final(PaymentStatus.REFUNDED)
        assert transitions.is_final(PaymentStatus.CHARGED_BACK)
        assert not transitions.is_final(PaymentStatus.REPORTED)


class TestDepositPolicy:
    """RN-PAG-001 e RN-GST-004."""

    def test_the_deposit_is_fifty_euro(self) -> None:
        assert str(DepositPolicy().amount()) == "50.00"

    def test_every_ordinary_booking_requires_a_deposit(self) -> None:
        policy = DepositPolicy()

        assert policy.requires_deposit(UserRole.RESIDENT, belongs_to_quoted_work=False)
        assert policy.requires_deposit(UserRole.OWNER, belongs_to_quoted_work=False)
        assert policy.requires_deposit(UserRole.MANAGER, belongs_to_quoted_work=True)

    def test_a_guest_own_client_does_not(self) -> None:
        """RN-GST-004: o guest recebe diretamente e esses valores nao passam
        pelo estudio. Sem orcamento ligado, o atendimento e dele."""
        assert not DepositPolicy().requires_deposit(
            UserRole.GUEST, belongs_to_quoted_work=False
        )

    def test_a_studio_referral_to_a_guest_does(self) -> None:
        """RN-GST-005: o cliente paga ao estudio, que fica com 50%. O orcamento
        so existe porque o gestor o criou (RN-ORC-001)."""
        assert DepositPolicy().requires_deposit(UserRole.GUEST, belongs_to_quoted_work=True)


class TestBookingSettlement:
    """RN-PAG-003, RN-AGE-008, RN-AGE-009 e RN-AGE-010."""

    def test_the_studio_returns_everything_when_it_rejects(self) -> None:
        outcome = BookingSettlement().decide(SettlementEvent.REJECTED_BY_STUDIO)

        assert outcome.refund_deposit
        assert outcome.refund_above_deposit
        assert not outcome.retain_deposit

    def test_cancelling_keeps_the_deposit_even_with_notice(self) -> None:
        """RN-AGE-009: o sinal fica com o estudio mesmo com aviso de 24 horas,
        para compensar o horario reservado e a preparacao do desenho."""
        outcome = BookingSettlement().decide(SettlementEvent.CANCELLED)

        assert outcome.retain_deposit
        assert outcome.refund_above_deposit
        assert not outcome.refund_deposit

    def test_a_no_show_settles_like_a_cancellation(self) -> None:
        settlement = BookingSettlement()

        assert settlement.decide(SettlementEvent.NO_SHOW) == settlement.decide(
            SettlementEvent.CANCELLED
        )

    def test_rescheduling_in_time_moves_everything_along(self) -> None:
        outcome = BookingSettlement().decide(SettlementEvent.RESCHEDULED_IN_TIME)

        assert outcome.keeps_everything

    def test_rescheduling_late_costs_the_deposit(self) -> None:
        outcome = BookingSettlement().decide(SettlementEvent.RESCHEDULED_LATE)

        assert outcome.retain_deposit
        assert outcome.refund_above_deposit

    def test_every_event_carries_a_reason_for_the_record(self) -> None:
        settlement = BookingSettlement()

        for event in SettlementEvent:
            assert settlement.reason(event).strip()


class TestRescheduleNotice:
    """RN-AGE-008: o prazo de 24 horas conta contra o horario marcado."""

    def test_more_than_a_day_ahead_is_in_time(self) -> None:
        outcome = RescheduleNotice().outcome(APPOINTMENT, APPOINTMENT - timedelta(hours=30))

        assert outcome == BookingOutcome.RESCHEDULED_IN_TIME

    def test_exactly_twenty_four_hours_is_in_time(self) -> None:
        """"Pelo menos 24 horas" inclui as 24 horas cheias."""
        outcome = RescheduleNotice().outcome(APPOINTMENT, APPOINTMENT - timedelta(hours=24))

        assert outcome == BookingOutcome.RESCHEDULED_IN_TIME

    def test_a_minute_short_is_late(self) -> None:
        outcome = RescheduleNotice().outcome(
            APPOINTMENT, APPOINTMENT - timedelta(hours=23, minutes=59)
        )

        assert outcome == BookingOutcome.RESCHEDULED_LATE

    def test_after_the_appointment_is_late(self) -> None:
        outcome = RescheduleNotice().outcome(APPOINTMENT, APPOINTMENT + timedelta(hours=1))

        assert outcome == BookingOutcome.RESCHEDULED_LATE
