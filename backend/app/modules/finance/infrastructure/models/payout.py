import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase
from app.modules.finance.domain.payout_status import PayoutStatus


class Payout(OrmBase):
    """O repasse de uma semana a um artista (RN-REP-004 e RN-REP-007).

    `period_end` é a sexta às 20h `Europe/Dublin` convertida para UTC. Guardar o
    instante e não a data evita a pergunta "20h de qual fuso" toda vez que
    alguém lê a linha — e o horário de verão irlandês move esse instante duas
    vezes por ano.

    **`net_total` é redundante de propósito e o banco garante a conta.** Ele
    poderia ser somado na leitura, mas é o número que o artista recebe: deixá-lo
    derivado faria cada tela repetir a soma, e bastaria uma errar para o
    demonstrativo discordar do extrato. A restrição `ck_payout_net_total` o
    mantém igual a `gross_total + adjustments_total`, e os ajustes são negativos.

    **Os totais são fotografia, não espelho.** Um repasse já pago não muda quando
    um pagamento é devolvido depois: a RN-REP-005 manda lançar a parcela como
    ajuste negativo no repasse **seguinte**, e é por isso que o fechamento
    anterior permanece intocado."""

    __tablename__ = "payout"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False, index=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    gross_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    adjustments_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PayoutStatus] = mapped_column(String(16), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True
    )
    receipt_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
