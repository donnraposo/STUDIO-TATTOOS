"""Habilita as extensoes exigidas pelo modelo de dados

btree_gist permite combinar igualdade com sobreposicao de intervalo na mesma
restricao EXCLUDE, base das duas regras de nao sobreposicao da agenda.
citext garante e-mail unico sem diferenciar maiusculas.

Ver DOCS/05_MODELO_DADOS.md secao 2.

Revision ID: 0001
Revises:
Create Date: 2026-09-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS citext")
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
