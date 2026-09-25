"""Identidade, sessoes e trilha de auditoria

Cria as tabelas da Sprint 02 e aplica a imutabilidade da auditoria no proprio
banco: a role da aplicacao perde UPDATE e DELETE em audit_log (ADR-012).

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_account",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("artist_name", sa.String(160), nullable=True),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("acts_as_artist", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("requested_role", sa.String(16), nullable=True),
        sa.Column(
            "created_by",
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
        sa.CheckConstraint(
            "role IN ('OWNER', 'MANAGER', 'RESIDENT', 'GUEST')", name="ck_user_account_role"
        ),
        sa.CheckConstraint(
            "status IN ('PENDING_APPROVAL', 'ACTIVE', 'BLOCKED', 'REJECTED')",
            name="ck_user_account_status",
        ),
        sa.CheckConstraint(
            "NOT (acts_as_artist OR role IN ('RESIDENT', 'GUEST')) OR artist_name IS NOT NULL",
            name="ck_user_account_artist_name_required",
        ),
    )

    op.create_table(
        "user_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(320), nullable=True),
    )
    op.create_index("ix_user_session_user_id", "user_session", ["user_id"])

    op.create_table(
        "user_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(24), nullable=True),
        sa.Column("to_status", sa.String(24), nullable=False),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_user_status_history_user_id", "user_status_history", ["user_id"])

    op.create_table(
        "password_reset_token",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_password_reset_token_user_id", "password_reset_token", ["user_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("module", sa.String(40), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(80), nullable=True),
        sa.Column("old_values", postgresql.JSONB(), nullable=True),
        sa.Column("new_values", postgresql.JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_module", "audit_log", ["module"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    # ADR-012: imutabilidade garantida pelo banco, nao pela aplicacao.
    #
    # REVOKE sozinho seria insuficiente: a role da aplicacao e dona da tabela e
    # poderia conceder o privilegio de volta a si mesma. O gatilho abaixo recusa
    # UPDATE e DELETE para qualquer role, inclusive a dona, e so pode ser
    # contornado removendo-o explicitamente por DDL.
    op.execute("REVOKE UPDATE, DELETE ON TABLE audit_log FROM PUBLIC")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_is_append_only()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_log e append-only: % nao e permitido (ADR-012)', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_append_only
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_is_append_only();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_append_only ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS audit_log_is_append_only()")
    op.drop_table("audit_log")
    op.drop_table("password_reset_token")
    op.drop_table("user_status_history")
    op.drop_table("user_session")
    op.drop_table("user_account")
