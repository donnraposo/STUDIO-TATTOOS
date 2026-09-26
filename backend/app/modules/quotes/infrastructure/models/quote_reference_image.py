import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase


class QuoteReferenceImage(OrmBase):
    """Imagem de referência de um orçamento (RN-ORC-004).

    Guarda **apenas a chave privada do objeto**, nunca uma URL pública. A
    referência é a tatuagem que o cliente quer e fica associada ao nome dele;
    um endereço público permanente seria exposição de dado pessoal a quem
    descobrisse o link. O acesso passa pelo backend, que confere a sessão antes
    de devolver um endereço temporário (ADR-006).

    `content_type` e `byte_size` são gravados no momento do upload, e não
    deduzidos do arquivo depois, para que a listagem de um orçamento não precise
    consultar o armazenamento uma vez por imagem."""

    __tablename__ = "quote_reference_image"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote.id"), nullable=False, index=True
    )
    object_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
