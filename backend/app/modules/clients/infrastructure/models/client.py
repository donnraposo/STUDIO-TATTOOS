import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase


class Client(OrmBase):
    """Cliente do estudio. Nao possui conta nem acesso ao sistema.

    `registered_by_artist_id` determina a visibilidade da ficha completa
    (RN-CLI-004): o artista ve por inteiro apenas quem ele cadastrou.

    Exclusao direta e proibida quando ha historico (RN-CLI-006). O caminho e a
    anonimizacao, que preenche `anonymized_at` e limpa o contato preservando os
    registros financeiros."""

    __tablename__ = "client"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    instagram: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    registered_by_artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False, index=True
    )
    merged_into_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client.id"), nullable=True, index=True
    )
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
