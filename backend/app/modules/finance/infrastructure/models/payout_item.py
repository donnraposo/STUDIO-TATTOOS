import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase


class PayoutItem(OrmBase):
    """Uma sessão dentro de um repasse (RN-REP-003 e RN-REP-007).

    **`percentage` é copiado, não consultado.** É o percentual que estava
    congelado na sessão no momento do fechamento (RN-REP-006). Ler o orçamento na
    hora de exibir o demonstrativo mostraria o acordo de hoje sobre um
    pagamento de semanas atrás — e o artista veria um número diferente do que
    recebeu.

    **`amount` é guardado e não recalculado**, pelo mesmo motivo e mais um: a
    RN-REP-007 manda arredondar por sessão, e recalcular na leitura abriria a
    chance de alguém somar antes e arredondar depois, chegando a outro total.

    `uq_payout_item_session` impede a mesma sessão em dois repasses. Pagar duas
    vezes pelo mesmo trabalho aparece no extrato do estúdio, não num teste."""

    __tablename__ = "payout_item"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payout.id"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tattoo_session.id"), nullable=False
    )
    received_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
