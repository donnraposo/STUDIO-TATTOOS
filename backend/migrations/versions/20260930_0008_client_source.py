"""Cliente guarda quem o trouxe ao estudio

A RN-CLI-002 decide o dinheiro a partir de uma pergunta que o sistema nao sabia
responder: *"o cliente retornou ao mesmo artista **que o trouxe**?"*. O que
existia era `registered_by_artist_id`, e ele responde outra coisa -- quem digitou
o cadastro. Sao iguais quando o artista cadastra o proprio cliente e diferentes
justamente no caso que importa: a RN-GST-005 manda o **gestor** cadastrar o
cliente indicado pelo estudio, e ali o campo antigo aponta para o gestor, que nao
trouxe ninguem.

`brought_by_artist_id` nulo significa **indicacao do estudio**: o cliente chegou
ao salao, nao pela mao de um artista. A ausencia e o dado, e nao a falta dele.

**Os dois campos convivem porque respondem a perguntas diferentes.** A RN-CLI-004
amarra a visibilidade da ficha a quem cadastrou -- "o artista ve por inteiro
apenas quem ele cadastrou" --, e trocar um pelo outro mudaria quem enxerga o que.
Um cliente de indicacao do estudio ficaria sem dono e nenhum artista veria a
ficha dele.

**Isto nao decide a origem do atendimento.** A RN-CLI-002 e explicita: "a origem
sera determinada em cada atendimento". O mesmo cliente volta pelo artista que o
trouxe numa vez e e encaminhado pelo estudio na seguinte. O campo alimenta a
sugestao do formulario de orcamento; quem decide continua sendo quem orca, e
corrigir e do gestor (RN-CLI-003).

**Os cadastros existentes ficam com nulo**, e isso e correto e nao uma lacuna: o
sistema nao sabe quem os trouxe, e inventar o artista que cadastrou como se fosse
quem trouxe gravaria uma afirmacao que ninguem fez -- e ela sairia do banco como
verdade no primeiro repasse.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "client",
        sa.Column(
            "brought_by_artist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
    )
    op.create_index("ix_client_brought_by_artist_id", "client", ["brought_by_artist_id"])


def downgrade() -> None:
    op.drop_index("ix_client_brought_by_artist_id", table_name="client")
    op.drop_column("client", "brought_by_artist_id")
