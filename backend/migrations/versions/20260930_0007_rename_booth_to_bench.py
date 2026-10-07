"""Maca passa a se chamar bench, e nao booth

O estudio corrigiu o termo em ingles: a unidade reservavel e uma **bench**, nao
uma booth. `booth` descreve uma cabine fechada, que nao e o que existe no salao.

Renomear e nao apenas rotular na tela. O nome errado no banco sobrevive a
qualquer correcao de interface e reaparece em cada consulta, cada log e cada
migracao futura -- e a proxima pessoa a ler o esquema aprende o termo errado.

**As restricoes sao renomeadas junto, e isso nao e cosmetico.** O
`BookingRepository` traduz a violacao de `booking_booth_no_overlap` no `scope`
que alimenta o modal da RN-AGE-007; o nome da restricao e contrato entre o banco
e a aplicacao. Deixa-lo para tras faria o codigo procurar por um nome que o banco
nao usa mais, e o conflito voltaria como erro generico -- com a agenda
funcionando em tudo, menos justamente na regra que ela existe para garantir.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Nomes que o PostgreSQL gerou sozinho e que `RENAME` nao acompanha. Ficam aqui
#: como dados para que ida e volta sejam a mesma lista lida ao contrario.
_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("INDEX", "ix_booking_booth_id", "ix_booking_bench_id"),
    ("INDEX", "booth_pkey", "bench_pkey"),
    ("INDEX", "booth_number_key", "bench_number_key"),
)


def upgrade() -> None:
    op.rename_table("booth", "bench")
    op.alter_column("booking", "booth_id", new_column_name="bench_id")

    for kind, old, new in _RENAMES:
        op.execute(f"ALTER {kind} IF EXISTS {old} RENAME TO {new}")

    op.execute(
        "ALTER TABLE booking RENAME CONSTRAINT booking_booth_id_fkey TO booking_bench_id_fkey"
    )
    op.execute(
        "ALTER TABLE booking RENAME CONSTRAINT booking_booth_no_overlap"
        " TO booking_bench_no_overlap"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE booking RENAME CONSTRAINT booking_bench_no_overlap"
        " TO booking_booth_no_overlap"
    )
    op.execute(
        "ALTER TABLE booking RENAME CONSTRAINT booking_bench_id_fkey TO booking_booth_id_fkey"
    )

    for kind, old, new in _RENAMES:
        op.execute(f"ALTER {kind} IF EXISTS {new} RENAME TO {old}")

    op.alter_column("booking", "bench_id", new_column_name="booth_id")
    op.rename_table("bench", "booth")
