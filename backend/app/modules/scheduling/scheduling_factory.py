from collections.abc import Callable

from sqlalchemy.orm import Session

from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.application.approve_booking import ApproveBooking
from app.modules.scheduling.application.cancel_booking import CancelBooking
from app.modules.scheduling.application.create_booth import CreateBooth
from app.modules.scheduling.application.list_bookings import ListBookings
from app.modules.scheduling.application.reject_booking import RejectBooking
from app.modules.scheduling.application.request_booking import RequestBooking
from app.modules.scheduling.application.reschedule_booking import RescheduleBooking
from app.modules.scheduling.domain.booking_settlement_gate import BookingSettlementGate
from app.modules.scheduling.domain.deposit_gate import DepositGate
from app.modules.scheduling.domain.reschedule_notice import RescheduleNotice
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository
from app.modules.scheduling.infrastructure.booth_repository import BoothRepository


class SchedulingFactory:
    """Monta os casos de uso da agenda.

    Recebe **fábricas das portas**, e não o módulo financeiro. A agenda declara
    o contrato de que precisa — `DepositGate` e `BookingSettlementGate` — e a
    raiz de composição liga quem o cumpre (ADR-016). Importar a fábrica do
    financeiro aqui inverteria a direção: a regra de aprovação passaria a
    depender do desenho interno de pagamento.

    São funções de `Session` e não instâncias prontas porque as portas carregam
    repositórios, e repositório pertence à transação em curso."""

    def __init__(
        self,
        deposit_gate: Callable[[Session], DepositGate],
        settlement_gate: Callable[[Session], BookingSettlementGate],
    ) -> None:
        self._policy = SchedulingPolicy()
        self._notice = RescheduleNotice()
        self._deposit_gate = deposit_gate
        self._settlement_gate = settlement_gate

    @property
    def policy(self) -> SchedulingPolicy:
        return self._policy

    def bookings(self, session: Session) -> BookingRepository:
        return BookingRepository(session)

    def booths(self, session: Session) -> BoothRepository:
        return BoothRepository(session)

    def request_booking(self, session: Session) -> RequestBooking:
        return RequestBooking(
            bookings=self.bookings(session),
            booths=self.booths(session),
            policy=self._policy,
            deposits=self._deposit_gate(session),
            audit=AuditRecorder(session),
        )

    def approve_booking(self, session: Session) -> ApproveBooking:
        return ApproveBooking(
            bookings=self.bookings(session),
            policy=self._policy,
            deposits=self._deposit_gate(session),
            audit=AuditRecorder(session),
        )

    def reject_booking(self, session: Session) -> RejectBooking:
        return RejectBooking(
            bookings=self.bookings(session),
            policy=self._policy,
            settlement=self._settlement_gate(session),
            audit=AuditRecorder(session),
        )

    def cancel_booking(self, session: Session) -> CancelBooking:
        return CancelBooking(
            bookings=self.bookings(session),
            policy=self._policy,
            settlement=self._settlement_gate(session),
            audit=AuditRecorder(session),
        )

    def reschedule_booking(self, session: Session) -> RescheduleBooking:
        return RescheduleBooking(
            bookings=self.bookings(session),
            booths=self.booths(session),
            policy=self._policy,
            notice=self._notice,
            settlement=self._settlement_gate(session),
            audit=AuditRecorder(session),
        )

    def list_bookings(self, session: Session) -> ListBookings:
        return ListBookings(bookings=self.bookings(session), policy=self._policy)

    def create_booth(self, session: Session) -> CreateBooth:
        return CreateBooth(
            booths=self.booths(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )
