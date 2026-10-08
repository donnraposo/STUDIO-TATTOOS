import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.modules.scheduling.domain.booking_status import BookingStatus
from app.modules.scheduling.domain.deposit_gate import DepositGate
from app.modules.scheduling.domain.scheduling_policy import SchedulingPolicy
from app.modules.scheduling.infrastructure.bench_repository import BenchRepository
from app.modules.scheduling.infrastructure.booking_repository import BookingRepository
from app.modules.scheduling.infrastructure.models.booking import Booking
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class RequestBooking:
    """Cria um agendamento.

    Residente e guest sempre criam em `REQUESTED`; o gestor pode criar já em
    `APPROVED` (RN-AGE-005). A diferença importa para as restrições do banco:
    pendente não bloqueia a maca para outros artistas, aprovado bloqueia.

    Nenhuma verificação de conflito acontece aqui de propósito — quem decide é a
    restrição `EXCLUDE`, no momento da gravação. Conferir antes e gravar depois
    abriria a janela de corrida que o ADR-011 fecha.

    **Criar já aprovado só vale onde não há sinal a confirmar.** A RN-AGE-005
    permite ao gestor criar em `APPROVED` *"desde que confirmem o sinal"*, e o
    sinal pertence ao agendamento (RN-PAG-001) — que ainda não existe no instante
    da criação. Não há, portanto, sinal confirmado a apresentar: o gestor cria em
    `REQUESTED`, registra e confirma os €50, e aprova. O atalho continua aberto
    exatamente onde a regra não pede sinal: cliente próprio do guest
    (RN-GST-004)."""

    def __init__(
        self,
        bookings: BookingRepository,
        benches: BenchRepository,
        policy: SchedulingPolicy,
        deposits: DepositGate,
        audit: AuditRecorder,
    ) -> None:
        self._bookings = bookings
        self._benches = benches
        self._policy = policy
        self._deposits = deposits
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        client_id: uuid.UUID,
        bench_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        artist_id: uuid.UUID | None = None,
        approve_immediately: bool = False,
        quote_id: uuid.UUID | None = None,
        deposit_amount: Decimal | None = None,
    ) -> Booking:
        if not self._policy.can_request(actor):
            raise PermissionDeniedError("You cannot create bookings.")

        if ends_at <= starts_at:
            raise BusinessRuleError("The end time must be after the start time.")

        bench = self._benches.find_by_id(bench_id)
        if bench is None or not bench.active:
            raise BusinessRuleError("Bench not found or inactive.")

        target_artist = self._resolve_artist(actor, artist_id)
        status = self._resolve_status(actor, target_artist, approve_immediately)

        booking = Booking(
            client_id=client_id,
            artist_id=target_artist,
            bench_id=bench_id,
            period=self._bookings.build_period(starts_at, ends_at),
            status=status,
            # O trabalho orcado que este horario atende. Nulo quando nao ha
            # orcamento: o guest nao acessa o modulo (RN-ORC-001) e agenda para
            # clientes proprios sem nenhum.
            quote_id=quote_id,
            # O sinal que o artista informou. Nulo cai no padrao do estudio:
            # quem nao disse nada nao esta dizendo "sem sinal".
            deposit_amount=deposit_amount,
            decided_at=datetime.now(UTC) if status == BookingStatus.APPROVED else None,
            decided_by=actor.id if status == BookingStatus.APPROVED else None,
        )
        self._bookings.persist(booking)

        self._audit.record(
            actor_id=actor.id,
            action="BOOKING_CREATED",
            module="scheduling",
            entity_type="booking",
            entity_id=str(booking.id),
            new_values={"status": str(status), "bench_id": str(bench_id)},
        )
        return booking

    def _resolve_artist(
        self, actor: AuthenticatedUser, artist_id: uuid.UUID | None
    ) -> uuid.UUID:
        """O artista agenda para si; o gestor agenda para qualquer um."""
        if artist_id is None:
            return actor.id
        if artist_id != actor.id and not actor.is_staff:
            raise PermissionDeniedError("You cannot book on behalf of another artist.")
        return artist_id

    def _resolve_status(
        self, actor: AuthenticatedUser, artist_id: uuid.UUID, approve_immediately: bool
    ) -> BookingStatus:
        """O agendamento nasce sem sessão ligada, então nunca pertence a um
        trabalho orçado no instante da criação — é por isso que a pergunta ao
        portão passa `False`."""
        if not approve_immediately:
            return BookingStatus.REQUESTED

        if not self._policy.can_create_already_approved(actor):
            raise PermissionDeniedError("You cannot create an approved booking.")

        if self._deposits.is_required_for(artist_id, belongs_to_quoted_work=False):
            raise BusinessRuleError(
                "This booking needs the €50 deposit confirmed before approval."
                " Create the request, confirm the deposit, then approve it."
            )
        return BookingStatus.APPROVED
