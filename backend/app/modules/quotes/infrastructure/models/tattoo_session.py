import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase
from app.modules.quotes.domain.quote_origin import QuoteOrigin
from app.modules.quotes.domain.session_status import SessionStatus


class TattooSession(OrmBase):
    """Uma sessão prevista pelo orçamento, e a unidade de cálculo do repasse.

    A tabela se chama `tattoo_session`, e não `session` como constava no modelo
    de dados: neste projeto `Session` já é a sessão de banco do SQLAlchemy,
    importada em todo repositório, e `user_session` é a sessão de login. Três
    coisas diferentes com o mesmo nome é confusão garantida na leitura.

    `origin` e `artist_percentage` são **cópias** do orçamento no momento da
    aprovação, não consultas ao orçamento na hora do repasse (RN-REP-006). O
    orçamento pode voltar a pendente e ser reaprovado com outro percentual; o
    que já foi executado continua valendo o que valia.

    `charged_value` é o valor efetivamente cobrado e pode divergir de
    `planned_value` em sessão parcial (RN-ORC-006) — é sobre ele, e não sobre o
    previsto, que o repasse é calculado.

    `performed_at` é a data real da sessão, não a agendada: é dela que sai o
    vencimento do pós-venda em 15 dias (RN-POS-001)."""

    __tablename__ = "tattoo_session"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote.id"), nullable=False, index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SessionStatus] = mapped_column(String(20), nullable=False, index=True)
    origin: Mapped[QuoteOrigin] = mapped_column(String(16), nullable=False)
    planned_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    charged_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    artist_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    marked_done_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
