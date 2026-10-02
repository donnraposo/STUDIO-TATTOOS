"""Repasses semanais, itens por sessao e ajustes

Tres garantias desta migracao existem porque a aplicacao sozinha nao basta para
sustenta-las ao longo do tempo:

1. **Uma semana fecha uma vez por artista** (RN-REP-004). `uq_payout_period`
   sobre `(artist_id, period_end)` e o que impede dois fechamentos da mesma
   sexta-feira -- e esse e o risco declarado da sprint. A garantia e do banco e
   nao da garantia de que so existe um processo calculando: com o calculo sob
   demanda, duas abas abertas na tela de repasses sao dois processos.

2. **Uma sessao entra em um repasse so.** `uq_payout_item_session` impede pagar
   duas vezes pelo mesmo trabalho. Sem ela, um recalculo que nao limpasse o
   anterior dobraria silenciosamente o que o artista recebe, e o erro apareceria
   no extrato bancario do estudio, nao num teste.

3. **Ajuste e negativo, item e positivo.** A RN-REP-005 manda lancar a parcela
   ja repassada como ajuste negativo no repasse seguinte; um ajuste positivo
   seria outra coisa, sem regra que o preveja, e um item negativo seria um
   repasse que cobra do artista.

**`period_end` e a sexta as 20h `Europe/Dublin` convertida para UTC**, como o
modelo de dados registra. Guardar o instante e nao a data evita a pergunta "20h
de qual fuso" toda vez que alguem ler a linha -- e o horario de verao irlandes
move esse instante duas vezes por ano.

**`receipt_object_key` e opcional** (RN-REP-007): o comprovante da transferencia
pode existir ou nao, e exigi-lo impediria registrar um repasse pago em dinheiro.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payout",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "artist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gross_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("adjustments_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "paid_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column("receipt_object_key", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        # RN-REP-004: uma semana fecha uma vez por artista.
        sa.UniqueConstraint("artist_id", "period_end", name="uq_payout_period"),
        sa.CheckConstraint(
            "status IN ('CALCULATED', 'PAID', 'ADJUSTED')", name="ck_payout_status"
        ),
        sa.CheckConstraint("period_end > period_start", name="ck_payout_period_not_empty"),
        # RN-REP-007: o liquido e o bruto mais os ajustes, que sao negativos.
        sa.CheckConstraint(
            "net_total = gross_total + adjustments_total", name="ck_payout_net_total"
        ),
        sa.CheckConstraint("gross_total >= 0", name="ck_payout_gross_not_negative"),
        sa.CheckConstraint(
            "adjustments_total <= 0", name="ck_payout_adjustments_not_positive"
        ),
        # RN-REP-004: pago sem quem confirmou e quando e dinheiro que saiu sem
        # ninguem por tras dele.
        sa.CheckConstraint(
            "status <> 'PAID' OR (paid_at IS NOT NULL AND paid_by IS NOT NULL)",
            name="ck_payout_paid_requires_actor",
        ),
    )
    op.create_index("ix_payout_artist_id", "payout", ["artist_id"])
    op.create_index("ix_payout_period_end", "payout", ["period_end"])

    op.create_table(
        "payout_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payout_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payout.id"), nullable=False
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tattoo_session.id"),
            nullable=False,
        ),
        sa.Column("received_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        # Uma sessao entra em um repasse so: pagar duas vezes pelo mesmo
        # trabalho aparece no extrato do estudio, nao num teste.
        sa.UniqueConstraint("session_id", name="uq_payout_item_session"),
        sa.CheckConstraint("received_amount > 0", name="ck_payout_item_received_positive"),
        sa.CheckConstraint(
            "percentage > 0 AND percentage <= 100", name="ck_payout_item_percentage_range"
        ),
        sa.CheckConstraint("amount >= 0", name="ck_payout_item_amount_not_negative"),
    )
    op.create_index("ix_payout_item_payout_id", "payout_item", ["payout_id"])

    op.create_table(
        "payout_adjustment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payout_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payout.id"), nullable=False
        ),
        sa.Column(
            "related_payment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payment.id"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        # RN-REP-005: o ajuste desconta o que ja foi repassado.
        sa.CheckConstraint("amount < 0", name="ck_payout_adjustment_negative"),
        # Um pagamento devolvido gera um ajuste, nao varios.
        sa.UniqueConstraint("related_payment_id", name="uq_payout_adjustment_payment"),
    )
    op.create_index("ix_payout_adjustment_payout_id", "payout_adjustment", ["payout_id"])


def downgrade() -> None:
    op.drop_table("payout_adjustment")
    op.drop_table("payout_item")
    op.drop_table("payout")
