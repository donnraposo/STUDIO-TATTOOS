"""O sinal deixa de ser um valor unico do estudio

A RN-PAG-001 fixa o sinal em EUR 50. Na operacao isso deixou de valer: cada
artista cobra o seu, e o responsavel pediu em 08/10/2026 que o valor seja dito
por quem o recebeu.

**O numero nunca esteve sendo exigido.** O portao da RN-AGE-005 confere se
existe sinal **confirmado**, nao quanto ele vale, e a retencao da RN-AGE-009
marca o pagamento inteiro como retido -- qualquer que seja o valor. Os EUR 50
viviam no `DepositPolicy` como constante e em textos de tela, e e so isso que
muda de natureza: de regra para **padrao**.

`deposit_amount` e o valor que o artista informa ao marcar o horario. Nulo
significa "use o padrao do estudio", e e o caso de todo agendamento criado antes
desta data -- a coluna e opcional por isso, e nao por tolerancia.

**Nao e o pagamento.** O pagamento continua sendo a linha em `payment`, com o
valor que o gestor confirmou ter entrado. Este campo e a expectativa que o
artista registrou; os dois podem divergir, e e justamente isso que o gestor
corrige ao registrar -- o responsavel pediu que o campo chegue preenchido e
editavel.

**A RN-PAG-001 continua como esta no documento de regras.** A decisao do
responsavel a estende, e cabe a ele atualizar o texto -- este codigo nao
reescreve regra de negocio por conta propria.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "booking",
        sa.Column("deposit_amount", sa.Numeric(12, 2), nullable=True),
    )
    # Sinal negativo nao existe, e sinal zero e "sem sinal" -- que se diz
    # deixando a coluna nula, nao escrevendo zero nela.
    op.create_check_constraint(
        "ck_booking_deposit_amount_positive",
        "booking",
        "deposit_amount IS NULL OR deposit_amount > 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_booking_deposit_amount_positive", "booking", type_="check")
    op.drop_column("booking", "deposit_amount")
