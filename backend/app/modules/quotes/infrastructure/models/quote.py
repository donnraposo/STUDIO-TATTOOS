import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase
from app.modules.quotes.domain.quote_origin import QuoteOrigin
from app.modules.quotes.domain.quote_status import QuoteStatus


class Quote(OrmBase):
    """Orçamento de um trabalho, do qual nascem as sessões (RN-ORC-004).

    `artist_percentage` é o campo mais delicado da tabela. Fica nulo enquanto o
    orçamento está pendente e é **congelado na aprovação** (RN-REP-006): a
    partir daí, mudar o percentual padrão do estúdio não afeta este trabalho. A
    migração garante por restrição que orçamento aprovado não existe sem
    percentual gravado — sem isso, um repasse poderia ser calculado com o
    percentual vigente hoje sobre um trabalho aprovado meses atrás.

    `origin` decide o dinheiro e por isso também é copiado para cada sessão na
    aprovação, em vez de lido de volta daqui na hora do repasse.

    Valores monetários são `Numeric(12, 2)`, nunca ponto flutuante: repasse é
    dinheiro de terceiro e erro de arredondamento binário não é aceitável."""

    __tablename__ = "quote"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client.id"), nullable=False, index=True
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False, index=True
    )
    origin: Mapped[QuoteOrigin] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    body_region: Mapped[str] = mapped_column(String(80), nullable=False)
    size_estimate: Mapped[str] = mapped_column(String(80), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    planned_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_value_per_session: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[QuoteStatus] = mapped_column(String(16), nullable=False, index=True)
    artist_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
