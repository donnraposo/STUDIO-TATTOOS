"""O agendamento aponta para o orcamento que nasceu com ele

Ate aqui orcamento e agendamento eram criados em telas separadas e nao se
conheciam antes da aprovacao: `booking.session_id` so e preenchido depois que o
orcamento e aprovado e as sessoes existem.

A decisao de 07/10/2026 juntou os dois atos -- o tatuador escolhe a maca e
preenche os dados da tatuagem no mesmo formulario. Com isso o orcamento nasce
**junto** do agendamento, e passa a fazer falta um elo entre os dois antes de
qualquer aprovacao: sem ele, o gestor que abre o horario nao tem como aprovar o
orcamento dali, e a RN-ORC-002 exige que alguem o aprove.

**Nulo e caso legitimo, e nao falta de dado.** O guest nao acessa o modulo de
orcamentos (RN-ORC-001) e continua agendando para clientes proprios sem nenhum;
e os agendamentos criados antes desta data tambem nao tem. A coluna e opcional
por isso, e nao por tolerancia.

**Nao substitui `session_id`.** Os dois dizem coisas diferentes: `quote_id` diz
de qual trabalho este horario e, desde o pedido; `session_id` diz qual sessao
daquele trabalho foi marcada como realizada, e so existe depois da aprovacao.

`ondelete` fica em RESTRICT por omissao: apagar um orcamento que tem horario
marcado deixaria o horario orfao, e o banco recusa.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "booking",
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_booking_quote", "booking", "quote", ["quote_id"], ["id"]
    )
    # Indice porque a pergunta "quais horarios sao deste trabalho" e feita a
    # cada abertura do agendamento; sem ele seria varredura da tabela inteira.
    op.create_index("ix_booking_quote_id", "booking", ["quote_id"])


def downgrade() -> None:
    op.drop_index("ix_booking_quote_id", table_name="booking")
    op.drop_constraint("fk_booking_quote", "booking", type_="foreignkey")
    op.drop_column("booking", "quote_id")
