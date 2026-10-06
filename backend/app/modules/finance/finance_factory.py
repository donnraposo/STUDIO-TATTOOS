from collections.abc import Callable

from sqlalchemy.orm import Session

from app.modules.finance.application.close_weekly_payouts import CloseWeeklyPayouts
from app.modules.finance.application.compare_revenue_months import CompareRevenueMonths
from app.modules.finance.application.confirm_payment import ConfirmPayment
from app.modules.finance.application.confirm_payout_paid import ConfirmPayoutPaid
from app.modules.finance.application.get_payout_statement import GetPayoutStatement
from app.modules.finance.application.get_revenue_report import GetRevenueReport
from app.modules.finance.application.list_payments import ListPayments
from app.modules.finance.application.list_payments_by_status import ListPaymentsByStatus
from app.modules.finance.application.list_payouts import ListPayouts
from app.modules.finance.application.payment_decision import PaymentDecision
from app.modules.finance.application.payment_deposit_gate import PaymentDepositGate
from app.modules.finance.application.payment_settlement_gate import PaymentSettlementGate
from app.modules.finance.application.refund_payment import RefundPayment
from app.modules.finance.application.refuse_payment import RefusePayment
from app.modules.finance.application.register_payment import RegisterPayment
from app.modules.finance.application.settle_booking import SettleBooking
from app.modules.finance.domain.booking_settlement import BookingSettlement
from app.modules.finance.domain.deposit_policy import DepositPolicy
from app.modules.finance.domain.payment_policy import PaymentPolicy
from app.modules.finance.domain.payment_transition import PaymentTransition
from app.modules.finance.domain.payout_policy import PayoutPolicy
from app.modules.finance.domain.payout_share import PayoutShare
from app.modules.finance.domain.payout_week import PayoutWeek
from app.modules.finance.domain.revenue_ledger import RevenueLedger
from app.modules.finance.domain.revenue_month import RevenueMonth
from app.modules.finance.domain.revenue_policy import RevenuePolicy
from app.modules.finance.domain.settled_sessions import SettledSessions
from app.modules.finance.infrastructure.payment_refund_repository import (
    PaymentRefundRepository,
)
from app.modules.finance.infrastructure.payment_repository import PaymentRepository
from app.modules.finance.infrastructure.payout_adjustment_repository import (
    PayoutAdjustmentRepository,
)
from app.modules.finance.infrastructure.payout_item_repository import PayoutItemRepository
from app.modules.finance.infrastructure.payout_repository import PayoutRepository
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository


class FinanceFactory:
    """Monta os casos de uso do financeiro.

    Recebe a fábrica da porta `SettledSessions` e não o módulo de orçamentos: o
    repasse declara de que resposta precisa, e a raiz de composição liga quem a
    cumpre (ADR-028). Importar a fábrica de orçamentos aqui faria o cálculo do
    repasse depender do desenho interno daquele módulo.

    Também é quem constrói os dois adaptadores que a agenda consome por porta —
    `PaymentDepositGate` e `PaymentSettlementGate`. Eles vivem aqui, e não na
    agenda, porque implementam contrato dela com conhecimento daqui: é a única
    direção que mantém a agenda sem saber o que é um pagamento (ADR-016).

    As políticas são criadas uma vez e compartilhadas: são decisões puras, sem
    estado, e recriá-las por requisição só gastaria alocação."""

    def __init__(self, settled_sessions: Callable[[Session], SettledSessions]) -> None:
        self._policy = PaymentPolicy()
        self._transitions = PaymentTransition()
        self._deposits = DepositPolicy()
        self._settlement = BookingSettlement()
        self._payout_policy = PayoutPolicy()
        self._week = PayoutWeek()
        self._share = PayoutShare()
        self._revenue_policy = RevenuePolicy()
        self._months = RevenueMonth()
        self._ledger = RevenueLedger(self._share)
        self._settled_sessions = settled_sessions

    @property
    def policy(self) -> PaymentPolicy:
        return self._policy

    @property
    def deposits(self) -> DepositPolicy:
        return self._deposits

    def payments(self, session: Session) -> PaymentRepository:
        return PaymentRepository(session)

    def refunds(self, session: Session) -> PaymentRefundRepository:
        return PaymentRefundRepository(session)

    def decision(self, session: Session) -> PaymentDecision:
        return PaymentDecision(
            payments=self.payments(session),
            policy=self._policy,
            transitions=self._transitions,
        )

    def register_payment(self, session: Session) -> RegisterPayment:
        return RegisterPayment(
            payments=self.payments(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def confirm_payment(self, session: Session) -> ConfirmPayment:
        return ConfirmPayment(
            payments=self.payments(session),
            decision=self.decision(session),
            audit=AuditRecorder(session),
        )

    def refuse_payment(self, session: Session) -> RefusePayment:
        return RefusePayment(
            payments=self.payments(session),
            decision=self.decision(session),
            audit=AuditRecorder(session),
        )

    def refund_payment(self, session: Session) -> RefundPayment:
        return RefundPayment(
            payments=self.payments(session),
            refunds=self.refunds(session),
            decision=self.decision(session),
            audit=AuditRecorder(session),
        )

    def list_payments(self, session: Session) -> ListPayments:
        return ListPayments(
            payments=self.payments(session),
            bookings=BookingRepository(session),
            policy=self._policy,
        )

    def list_payments_by_status(self, session: Session) -> ListPaymentsByStatus:
        return ListPaymentsByStatus(payments=self.payments(session), policy=self._policy)

    def settle_booking(self, session: Session) -> SettleBooking:
        return SettleBooking(
            payments=self.payments(session),
            settlement=self._settlement,
            audit=AuditRecorder(session),
        )

    def deposit_gate(self, session: Session) -> PaymentDepositGate:
        return PaymentDepositGate(
            payments=self.payments(session),
            users=UserRepository(session),
            policy=self._deposits,
        )

    def settlement_gate(self, session: Session) -> PaymentSettlementGate:
        return PaymentSettlementGate(settle=self.settle_booking(session))

    def payouts(self, session: Session) -> PayoutRepository:
        return PayoutRepository(session)

    def payout_items(self, session: Session) -> PayoutItemRepository:
        return PayoutItemRepository(session)

    def payout_adjustments(self, session: Session) -> PayoutAdjustmentRepository:
        return PayoutAdjustmentRepository(session)

    def close_weekly_payouts(self, session: Session) -> CloseWeeklyPayouts:
        return CloseWeeklyPayouts(
            payouts=self.payouts(session),
            items=self.payout_items(session),
            sessions=self._settled_sessions(session),
            policy=self._payout_policy,
            week=self._week,
            share=self._share,
            audit=AuditRecorder(session),
        )

    def confirm_payout_paid(self, session: Session) -> ConfirmPayoutPaid:
        return ConfirmPayoutPaid(
            payouts=self.payouts(session),
            policy=self._payout_policy,
            audit=AuditRecorder(session),
        )

    def list_payouts(self, session: Session) -> ListPayouts:
        return ListPayouts(payouts=self.payouts(session), policy=self._payout_policy)

    def payout_statement(self, session: Session) -> GetPayoutStatement:
        return GetPayoutStatement(
            payouts=self.payouts(session),
            items=self.payout_items(session),
            adjustments=self.payout_adjustments(session),
            policy=self._payout_policy,
        )

    def revenue_report(self, session: Session) -> GetRevenueReport:
        return GetRevenueReport(
            sessions=self._settled_sessions(session),
            items=self.payout_items(session),
            ledger=self._ledger,
            months=self._months,
            policy=self._revenue_policy,
        )

    def compare_revenue(self, session: Session) -> CompareRevenueMonths:
        return CompareRevenueMonths(
            sessions=self._settled_sessions(session),
            items=self.payout_items(session),
            ledger=self._ledger,
            months=self._months,
            policy=self._revenue_policy,
        )
