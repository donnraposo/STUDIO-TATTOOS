import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase
from app.modules.finance.domain.payment_kind import PaymentKind
from app.modules.finance.domain.payment_method import PaymentMethod
from app.modules.finance.domain.payment_status import PaymentStatus


class Payment(OrmBase):
    """Um recebimento do estúdio (RN-PAG-001 a RN-PAG-009).

    **O valor nunca é editado.** A RN-PAG-007 é explícita: pagamento não se
    apaga e correção entra como lançamento de ajuste vinculado ao original. Por
    isso não há caminho de `UPDATE` de `amount` na aplicação — o que muda é o
    estado, e a devolução nasce como linha própria em `payment_refund`.

    **`booking_id` e `session_id` são origens exclusivas**, garantido por
    restrição. O sinal pertence ao agendamento, porque é o horário reservado que
    ele confirma (RN-PAG-001 e RN-AGE-005); o saldo pertence à sessão, porque é
    ela que é quitada (RN-PAG-008) e é por sessão que o repasse é calculado
    (RN-REP-003).

    **`retained_at` não é o mesmo que devolvido.** Um sinal retido continua
    `CONFIRMED`: o estúdio ficou com ele para compensar o horário reservado
    (RN-AGE-009). O que a marca faz é tirá-lo de cena como sinal *daquele*
    agendamento, para que uma remarcação fora do prazo exija um sinal novo
    (RN-AGE-008) em vez de reaproveitar o perdido."""

    __tablename__ = "payment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("booking.id"), nullable=True, index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tattoo_session.id"), nullable=True, index=True
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client.id"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    kind: Mapped[PaymentKind] = mapped_column(String(16), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(String(16), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(String(16), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reported_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True
    )
    refused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refused_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True
    )
    refusal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    retained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retained_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
