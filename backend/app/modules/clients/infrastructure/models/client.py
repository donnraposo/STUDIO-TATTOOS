import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase


class Client(OrmBase):
    """Cliente do estudio. Nao possui conta nem acesso ao sistema.

    Dois campos apontam para artistas, e respondem a perguntas diferentes.

    `registered_by_artist_id` determina a visibilidade da ficha completa
    (RN-CLI-004): o artista ve por inteiro apenas quem ele cadastrou.

    `brought_by_artist_id` diz quem **trouxe** o cliente ao estudio, e nulo
    significa indicacao do estudio -- a ausencia e o dado. E a pergunta que a
    RN-CLI-002 faz para decidir a origem do atendimento: "o cliente retornou ao
    mesmo artista que o trouxe?". Os dois coincidem quando o artista cadastra o
    proprio cliente e divergem no caso que importa: a RN-GST-005 manda o gestor
    cadastrar o cliente indicado pelo estudio, e ali quem cadastrou nao trouxe
    ninguem.

    **O campo sugere a origem; nao a decide.** A RN-CLI-002 e explicita: "a
    origem sera determinada em cada atendimento".

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
    brought_by_artist_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True, index=True
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
