"""Percentual padrao por artista

O estudio opera com tres divisoes, e nao duas: alem dos 70/30 de cliente
proprio e dos 50/50 de indicacao (RN-REP-001 e RN-REP-002), ha artistas que
ficam com **85%**. A planilha de controle do estudio mostra as tres convivendo
no mesmo mes, e o mesmo artista aparecendo em mais de uma.

**O percentual vira dado e deixa de ser codigo.** Ate aqui os dois valores
estavam fixos no `ArtistPercentagePolicy`, e acrescentar um terceiro seria
trocar uma rigidez por outra -- o estudio negocia acordos, e cada acordo novo
exigiria uma versao nova do sistema.

`default_artist_percentage` e **nulo por padrao**, e nulo significa "use a regra
da origem". Os artistas existentes continuam em 70/30 ou 50/50 sem que ninguem
precise preencher nada, e so quem tem acordo proprio ganha um valor aqui.

**Isto nao alcanca trabalho ja aprovado.** A RN-REP-006 e explicita: o percentual
e congelado na aprovacao do orcamento, e mudar o padrao depois nao toca no que
ja foi acordado. Este campo so decide o que a proxima aprovacao vai congelar.

**A RN-REP-001 e a RN-REP-002 continuam como estao no documento de regras.** A
decisao do responsavel em 06/10/2026 as estende, e cabe a ele atualizar o texto
-- este codigo nao reescreve regra de negocio por conta propria.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_account",
        sa.Column("default_artist_percentage", sa.Numeric(5, 2), nullable=True),
    )
    # Mesmo intervalo do percentual congelado no orcamento: zero seria trabalho
    # de graca e acima de cem seria o estudio pagando para trabalhar.
    op.create_check_constraint(
        "ck_user_account_percentage_range",
        "user_account",
        "default_artist_percentage IS NULL"
        " OR (default_artist_percentage > 0 AND default_artist_percentage <= 100)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_account_percentage_range", "user_account", type_="check")
    op.drop_column("user_account", "default_artist_percentage")
