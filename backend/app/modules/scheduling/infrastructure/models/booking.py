import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import TSTZRANGE, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase
from app.modules.scheduling.domain.booking_status import BookingStatus


class Booking(OrmBase):
    """Agendamento de uma maca por um artista em um intervalo.

    O intervalo é um `tstzrange` e não duas colunas soltas: é o que permite ao
    PostgreSQL recusar sobreposição por restrição `EXCLUDE`, em vez de confiar
    numa verificação da aplicação que duas requisições simultâneas contornam
    (ADR-011).

    Não há blocos fixos nem pausa obrigatória entre agendamentos da mesma maca
    (RN-AGE-001); o artista define início e fim."""

    __tablename__ = "booking"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client.id"), nullable=False, index=True
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False, index=True
    )
    booth_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("booth.id"), nullable=False, index=True
    )
    period: Mapped[object] = mapped_column(TSTZRANGE, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(String(16), nullable=False, index=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(24), nullable=True)
    rejection_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
