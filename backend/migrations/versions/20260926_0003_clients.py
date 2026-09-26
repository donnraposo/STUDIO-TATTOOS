"""Cadastro de clientes

Indices em telefone e Instagram sustentam o alerta de duplicidade da
RN-CLI-005, que avisa sem bloquear o cadastro.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("instagram", sa.String(80), nullable=True),
        sa.Column(
            "registered_by_artist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column(
            "merged_into_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("client.id"),
            nullable=True,
        ),
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_client_phone", "client", ["phone"])
    op.create_index("ix_client_instagram", "client", ["instagram"])
    op.create_index("ix_client_registered_by", "client", ["registered_by_artist_id"])
    op.create_index("ix_client_merged_into", "client", ["merged_into_id"])


def downgrade() -> None:
    op.drop_table("client")
