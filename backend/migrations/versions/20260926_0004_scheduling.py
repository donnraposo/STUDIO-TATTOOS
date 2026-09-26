"""Agenda: macas e agendamentos com integridade garantida pelo banco

As duas restricoes EXCLUDE desta migracao sao a hipotese tecnica central do
projeto (ADR-011). Elas tratam DOIS recursos com semanticas DIFERENTES:

  Maca    -> apenas agendamento APROVADO bloqueia. Solicitacoes pendentes de
             artistas diferentes podem concorrer pelo mesmo horario (RN-AGE-004).

  Artista -> PENDENTE e APROVADO bloqueiam, inclusive entre macas diferentes.
             O mesmo artista nao pode se comprometer em dois lugares ao mesmo
             tempo (RN-AGE-014).

Por que no banco e nao na aplicacao: duas requisicoes simultaneas podem ambas
consultar a agenda, ambas encontrar o horario livre e ambas gravar. Verificar em
codigo nao impede essa corrida; a restricao EXCLUDE impede, porque a segunda
gravacao falha na transacao.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "booth",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("number", sa.Integer(), nullable=False, unique=True),
        sa.Column("label", sa.String(80), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "booking",
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
        sa.Column(
            "booth_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("booth.id"), nullable=False
        ),
        sa.Column("period", postgresql.TSTZRANGE(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "decided_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column("rejection_reason", sa.String(24), nullable=True),
        sa.Column("rejection_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('REQUESTED', 'APPROVED', 'REJECTED', 'DONE', 'CANCELLED', 'NO_SHOW')",
            name="ck_booking_status",
        ),
        sa.CheckConstraint(
            "rejection_reason IS NULL OR rejection_reason IN "
            "('SLOT_TAKEN', 'STUDIO_CLOSED', 'RESCHEDULED')",
            name="ck_booking_rejection_reason",
        ),
        # O fim precisa ser posterior ao inicio; intervalo vazio nao e agendamento.
        sa.CheckConstraint("NOT isempty(period)", name="ck_booking_period_not_empty"),
    )
    op.create_index("ix_booking_client_id", "booking", ["client_id"])
    op.create_index("ix_booking_artist_id", "booking", ["artist_id"])
    op.create_index("ix_booking_booth_id", "booking", ["booth_id"])
    op.create_index("ix_booking_status", "booking", ["status"])

    # RN-AGE-004 e RN-AGE-007: a maca so e bloqueada por agendamento aprovado.
    op.execute(
        """
        ALTER TABLE booking ADD CONSTRAINT booking_booth_no_overlap
        EXCLUDE USING gist (booth_id WITH =, period WITH &&)
        WHERE (status = 'APPROVED')
        """
    )

    # RN-AGE-014: o artista nao pode ter pendencia ou aprovacao sobreposta,
    # mesmo em macas diferentes.
    op.execute(
        """
        ALTER TABLE booking ADD CONSTRAINT booking_artist_no_overlap
        EXCLUDE USING gist (artist_id WITH =, period WITH &&)
        WHERE (status IN ('REQUESTED', 'APPROVED'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE booking DROP CONSTRAINT IF EXISTS booking_artist_no_overlap")
    op.execute("ALTER TABLE booking DROP CONSTRAINT IF EXISTS booking_booth_no_overlap")
    op.drop_table("booking")
    op.drop_table("booth")
