import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase


class PayoutAdjustment(OrmBase):
    """Desconto de uma parcela já repassada (RN-REP-005).

    Uma devolução ocorrida **depois** de o repasse ter sido pago não altera o
    fechamento anterior: entra como ajuste negativo no seguinte. O valor é sempre
    negativo, garantido por restrição — um ajuste positivo seria outra coisa, sem
    regra que o preveja.

    `related_payment_id` é obrigatório e único: todo ajuste nasce de um pagamento
    devolvido, e um pagamento gera um ajuste, não vários. Sem a unicidade, dois
    fechamentos consecutivos poderiam descontar o mesmo valor duas vezes, e o
    artista pagaria em dobro por uma devolução só."""

    __tablename__ = "payout_adjustment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payout.id"), nullable=False, index=True
    )
    related_payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
