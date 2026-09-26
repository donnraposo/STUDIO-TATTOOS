"""Orcamentos, imagens de referencia e sessoes

Duas garantias desta migracao existem porque a aplicacao sozinha nao basta para
sustenta-las ao longo do tempo:

1. **Orcamento aprovado nao existe sem percentual congelado** (RN-REP-006). Se a
   restricao nao estivesse no banco, bastaria um caminho de aprovacao esquecer de
   gravar `artist_percentage` para que, meses depois, o repasse fosse calculado
   com o percentual vigente na data do calculo sobre um trabalho aprovado sob
   outro acordo. O erro apareceria no bolso do artista, nao num teste.

2. **Sessao parcial sem valor cobrado nao existe** (RN-ORC-006). O repasse de
   sessao parcial e calculado sobre o valor efetivamente recebido; um registro
   parcial com `charged_value` nulo nao tem sobre o que calcular.

A tabela se chama `tattoo_session` e nao `session` como constava em
05_MODELO_DADOS.md. O documento reservava explicitamente os nomes finais para a
revisao de implementacao, e `session` colidiria com a sessao de banco do
SQLAlchemy e com `user_session`, a sessao de login.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quote",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("client.id"), nullable=False
        ),
        sa.Column(
            "artist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("body_region", sa.String(80), nullable=False),
        sa.Column("size_estimate", sa.String(80), nullable=False),
        sa.Column("total_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("planned_sessions", sa.Integer(), nullable=False),
        sa.Column("planned_value_per_session", sa.Numeric(12, 2), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("artist_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("rejection_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_quote_status",
        ),
        sa.CheckConstraint(
            "origin IN ('ARTIST_OWN', 'STUDIO_REFERRAL')",
            name="ck_quote_origin",
        ),
        sa.CheckConstraint("total_value > 0", name="ck_quote_total_value_positive"),
        sa.CheckConstraint("planned_sessions >= 1", name="ck_quote_planned_sessions_positive"),
        sa.CheckConstraint(
            "planned_value_per_session > 0", name="ck_quote_planned_value_positive"
        ),
        sa.CheckConstraint(
            "estimated_duration_minutes > 0", name="ck_quote_duration_positive"
        ),
        sa.CheckConstraint(
            "artist_percentage IS NULL OR (artist_percentage > 0 AND artist_percentage <= 100)",
            name="ck_quote_percentage_range",
        ),
        # RN-REP-006: aprovar e congelar o percentual sao o mesmo ato.
        sa.CheckConstraint(
            "status <> 'APPROVED' OR (artist_percentage IS NOT NULL"
            " AND approved_at IS NOT NULL AND approved_by IS NOT NULL)",
            name="ck_quote_approved_freezes_percentage",
        ),
        # RN-ORC-003: rejeicao exige motivo; a observacao segue opcional.
        sa.CheckConstraint(
            "status <> 'REJECTED' OR rejection_reason IS NOT NULL",
            name="ck_quote_rejected_needs_reason",
        ),
    )
    op.create_index("ix_quote_client_id", "quote", ["client_id"])
    op.create_index("ix_quote_artist_id", "quote", ["artist_id"])
    op.create_index("ix_quote_status", "quote", ["status"])

    op.create_table(
        "quote_reference_image",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "quote_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quote.id"), nullable=False
        ),
        sa.Column("object_key", sa.String(512), nullable=False, unique=True),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("byte_size > 0", name="ck_quote_reference_image_byte_size_positive"),
    )
    op.create_index("ix_quote_reference_image_quote_id", "quote_reference_image", ["quote_id"])

    op.create_table(
        "tattoo_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "quote_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quote.id"), nullable=False
        ),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("planned_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("charged_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("artist_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "marked_done_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "confirmed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("quote_id", "sequence_number", name="uq_tattoo_session_sequence"),
        sa.CheckConstraint(
            "status IN ('SCHEDULED', 'DONE', 'PARTIALLY_DONE', 'PAID_OFF',"
            " 'CANCELLED', 'NO_SHOW')",
            name="ck_tattoo_session_status",
        ),
        sa.CheckConstraint(
            "origin IN ('ARTIST_OWN', 'STUDIO_REFERRAL')",
            name="ck_tattoo_session_origin",
        ),
        sa.CheckConstraint("sequence_number >= 1", name="ck_tattoo_session_sequence_positive"),
        sa.CheckConstraint("planned_value > 0", name="ck_tattoo_session_planned_value_positive"),
        sa.CheckConstraint(
            "charged_value IS NULL OR charged_value >= 0",
            name="ck_tattoo_session_charged_value_not_negative",
        ),
        sa.CheckConstraint(
            "artist_percentage > 0 AND artist_percentage <= 100",
            name="ck_tattoo_session_percentage_range",
        ),
        # RN-POS-001: o vencimento do pos-venda sai da data real da sessao.
        sa.CheckConstraint(
            "status NOT IN ('DONE', 'PARTIALLY_DONE', 'PAID_OFF')"
            " OR performed_at IS NOT NULL",
            name="ck_tattoo_session_performed_requires_date",
        ),
        # RN-ORC-006: o repasse parcial e calculado sobre o valor recebido.
        sa.CheckConstraint(
            "status <> 'PARTIALLY_DONE' OR charged_value IS NOT NULL",
            name="ck_tattoo_session_partial_requires_charged",
        ),
        # RN-ORC-005: so entra em repasse depois de o gestor confirmar.
        sa.CheckConstraint(
            "status <> 'PAID_OFF' OR (charged_value IS NOT NULL"
            " AND confirmed_at IS NOT NULL AND confirmed_by IS NOT NULL)",
            name="ck_tattoo_session_paid_off_requires_confirmation",
        ),
    )
    op.create_index("ix_tattoo_session_quote_id", "tattoo_session", ["quote_id"])
    op.create_index("ix_tattoo_session_status", "tattoo_session", ["status"])

    op.add_column(
        "booking",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tattoo_session.id"),
            nullable=True,
        ),
    )
    op.create_index("ix_booking_session_id", "booking", ["session_id"])

    # Uma sessao tem no maximo um agendamento vivo. Recusado e cancelado saem da
    # clausula, como nas restricoes EXCLUDE da 0004 (RN-AGE-014): remarcar
    # depois de cancelar continua possivel, executar a mesma sessao duas vezes
    # em horarios diferentes nao.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_booking_live_session ON booking (session_id)
        WHERE session_id IS NOT NULL AND status IN ('REQUESTED', 'APPROVED')
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_booking_live_session")
    op.drop_index("ix_booking_session_id", table_name="booking")
    op.drop_column("booking", "session_id")
    op.drop_table("tattoo_session")
    op.drop_table("quote_reference_image")
    op.drop_table("quote")
