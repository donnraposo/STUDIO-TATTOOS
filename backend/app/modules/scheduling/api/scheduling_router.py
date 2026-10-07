import uuid
from datetime import datetime

from fastapi import APIRouter, Request, status

from app.core.container import Container
from app.modules.identity.api.session_authenticator import SessionAuthenticator
from app.modules.scheduling.api.bench_request import BenchRequest
from app.modules.scheduling.api.bench_response import BenchResponse
from app.modules.scheduling.api.booking_request import BookingRequest
from app.modules.scheduling.api.booking_response import BookingResponse
from app.modules.scheduling.api.cancel_booking_request import CancelBookingRequest
from app.modules.scheduling.api.reject_booking_request import RejectBookingRequest
from app.modules.scheduling.api.reschedule_booking_request import RescheduleBookingRequest
from app.modules.scheduling.domain.booking_status import BookingStatus


class SchedulingRouter:
    """Agenda e macas (RN-AGE-001 a RN-AGE-014).

    Conflito de horário volta como 409 com o agendamento existente, para
    alimentar o modal que a RN-AGE-007 exige — aquele que não permite ignorar."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._authenticator = SessionAuthenticator(container)

    def build(self) -> APIRouter:
        router = APIRouter(tags=["scheduling"])
        router.add_api_route(
            "/benches", self.list_benches, methods=["GET"], response_model=list[BenchResponse]
        )
        router.add_api_route(
            "/benches",
            self.create_bench,
            methods=["POST"],
            response_model=BenchResponse,
            status_code=status.HTTP_201_CREATED,
        )
        router.add_api_route(
            "/bookings", self.list_bookings, methods=["GET"], response_model=list[BookingResponse]
        )
        router.add_api_route(
            "/bookings",
            self.request_booking,
            methods=["POST"],
            response_model=BookingResponse,
            status_code=status.HTTP_201_CREATED,
        )
        router.add_api_route(
            "/bookings/{booking_id}/approve",
            self.approve_booking,
            methods=["POST"],
            response_model=BookingResponse,
        )
        router.add_api_route(
            "/bookings/{booking_id}/reject",
            self.reject_booking,
            methods=["POST"],
            response_model=BookingResponse,
        )
        router.add_api_route(
            "/bookings/{booking_id}/cancel",
            self.cancel_booking,
            methods=["POST"],
            response_model=BookingResponse,
        )
        router.add_api_route(
            "/bookings/{booking_id}/reschedule",
            self.reschedule_booking,
            methods=["POST"],
            response_model=BookingResponse,
        )
        return router

    def list_benches(self, request: Request) -> list[BenchResponse]:
        self._authenticator.require_user(request)
        with self._container.database.session() as session:
            benches = self._container.scheduling.benches(session).list_all()
            return [BenchResponse.from_model(bench) for bench in benches]

    def create_bench(self, payload: BenchRequest, request: Request) -> BenchResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            bench = self._container.scheduling.create_bench(session).execute(
                actor=actor, label=payload.label
            )
            return BenchResponse.from_model(bench)

    def list_bookings(
        self,
        request: Request,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
        status: BookingStatus | None = None,
    ) -> list[BookingResponse]:
        """A agenda consulta um dia por vez, informando os dois extremos.

        Sem intervalo, devolve tudo — que e o uso de historico. A validacao de
        meia janela fica no caso de uso, nao aqui: e regra, nao formato."""
        actor = self._authenticator.require_user(request)
        with self._container.database.session() as session:
            bookings = self._container.scheduling.list_bookings(session).execute(
                actor, starts_at, ends_at, status
            )
            return [BookingResponse.from_model(booking) for booking in bookings]

    def request_booking(self, payload: BookingRequest, request: Request) -> BookingResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            booking = self._container.scheduling.request_booking(session).execute(
                actor=actor,
                client_id=payload.client_id,
                bench_id=payload.bench_id,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                artist_id=payload.artist_id,
                approve_immediately=payload.approve_immediately,
            )
            return BookingResponse.from_model(booking)

    def approve_booking(self, booking_id: uuid.UUID, request: Request) -> BookingResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            booking = self._container.scheduling.approve_booking(session).execute(
                actor=actor, booking_id=booking_id
            )
            return BookingResponse.from_model(booking)

    def reject_booking(
        self, booking_id: uuid.UUID, payload: RejectBookingRequest, request: Request
    ) -> BookingResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            booking = self._container.scheduling.reject_booking(session).execute(
                actor=actor, booking_id=booking_id, reason=payload.reason, note=payload.note
            )
            return BookingResponse.from_model(booking)

    def cancel_booking(
        self, booking_id: uuid.UUID, payload: CancelBookingRequest, request: Request
    ) -> BookingResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            booking = self._container.scheduling.cancel_booking(session).execute(
                actor=actor,
                booking_id=booking_id,
                reason=payload.reason,
                no_show=payload.no_show,
            )
            return BookingResponse.from_model(booking)

    def reschedule_booking(
        self, booking_id: uuid.UUID, payload: RescheduleBookingRequest, request: Request
    ) -> BookingResponse:
        actor = self._authenticator.require_user(request)
        self._container.csrf_guard.validate(request)
        with self._container.database.session() as session:
            booking = self._container.scheduling.reschedule_booking(session).execute(
                actor=actor,
                booking_id=booking_id,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                bench_id=payload.bench_id,
            )
            return BookingResponse.from_model(booking)
