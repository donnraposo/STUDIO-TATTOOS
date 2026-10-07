import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase
from app.modules.finance.domain.payment_method import PaymentMethod


class PaymentRefund(OrmBase):
    """Uma devolução, vinculada ao pagamento original (RN-PAG-009).

    É linha própria, e não um campo no pagamento, porque o lançamento original
    permanece preservado no histórico: quem olha precisa ver quanto entrou,
    quanto voltou e quanto o estúdio reteve — três números, não um saldo que
    apagou os outros dois.

    **`method` pode diferir do pagamento original.** A regra prevê isso: um
    depósito pode ser devolvido em dinheiro. Por isso a forma é própria da
    devolução e não herdada.

    `reason` é obrigatório. Devolução sem motivo registrado é dinheiro saindo do
    caixa sem explicação, e a RN-PAG-009 exige valor, data, forma, motivo e
    observação."""

    __tablename__ = "payment_refund"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    refunded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
