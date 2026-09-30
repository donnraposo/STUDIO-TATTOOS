"""Pagamentos, sinal e devolucoes

Tres garantias desta migracao existem porque a aplicacao sozinha nao basta para
sustenta-las ao longo do tempo:

1. **Pagamento confirmado nao existe sem quem confirmou e quando** (RN-PAG-002 e
   RN-PAG-007). Sem a restricao, bastaria um caminho gravar `CONFIRMED` sem
   responsavel para que um recebimento aparecesse no sistema sem ninguem por
   tras dele -- e e sobre recebimento confirmado que o repasse do artista e
   calculado.

2. **Um agendamento tem no maximo um sinal vivo** (RN-PAG-001). O indice parcial
   `uq_payment_live_deposit` impede dois sinais de EUR 50 valendo ao mesmo tempo
   para o mesmo horario. Recusado e retido saem da conta: depois de uma recusa o
   cliente paga outro sinal, e depois de uma remarcacao fora do prazo ele precisa
   pagar um novo (RN-AGE-008).

3. **Valor de pagamento nao se edita** (RN-PAG-007). Nao ha caminho de `UPDATE`
   de `amount` na aplicacao; correcao entra como `payment_refund` vinculado ao
   lancamento original, que permanece no historico.

**Duas colunas nao constavam na secao 7 de 05_MODELO_DADOS.md e entram aqui:**

- `booking_id`. O modelo previa `session_id` ou `guest_week_id` como unicas
  origens, mas a RN-PAG-001 diz "todo agendamento exigira um sinal de EUR 50", e
  `booking.session_id` e nulo em todo horario que nao pertence a um trabalho
  orcado -- e o caso de toda a agenda entregue na M3. Sem esta coluna, o sinal
  desses agendamentos nao tinha onde ser gravado, e a RN-AGE-005 nao tinha o que
  conferir antes de aprovar.

- `retained_at` / `retained_reason`. A RN-AGE-008 diz que, fora do prazo de 24
  horas, o cliente **perde** o sinal e precisa pagar um novo. O sinal perdido
  continua `CONFIRMED` -- o estudio ficou com ele, nao foi devolvido --, mas
  deixa de valer para a aprovacao daquele horario. Sem marcar essa retirada, o
  sinal velho continuaria satisfazendo o portao da RN-AGE-005 e o cliente
  aprovaria de novo sem pagar nada.

`guest_week_id` nao entra agora porque a tabela `guest_week` ainda nao existe:
ela nasce na sprint do guest, e a coluna entra junto com ela. Criar aqui uma
chave estrangeira para tabela inexistente quebraria a migracao.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "booking_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("booking.id"),
            nullable=True,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tattoo_session.id"),
            nullable=True,
        ),
        sa.Column(
            "client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("client.id"), nullable=True
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("receipt_object_key", sa.Text(), nullable=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "reported_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "confirmed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column("refused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "refused_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=True,
        ),
        sa.Column("refusal_reason", sa.Text(), nullable=True),
        sa.Column("retained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retained_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "kind IN ('DEPOSIT', 'BALANCE', 'FULL_PREPAY', 'GUEST_WEEK')",
            name="ck_payment_kind",
        ),
        sa.CheckConstraint(
            "method IN ('BANK_TRANSFER', 'CASH', 'CARD')",
            name="ck_payment_method",
        ),
        sa.CheckConstraint(
            "status IN ('REPORTED', 'CONFIRMED', 'REFUSED', 'REFUNDED', 'CHARGED_BACK')",
            name="ck_payment_status",
        ),
        sa.CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        # RN-PAG-002: o recebimento tem responsavel e hora. Confirmado sem os
        # dois e dinheiro que aparece no sistema sem ninguem por tras dele.
        sa.CheckConstraint(
            "status <> 'CONFIRMED' OR (confirmed_at IS NOT NULL AND confirmed_by IS NOT NULL)",
            name="ck_payment_confirmed_requires_actor",
        ),
        # RN-PAG-007: recusar e um ato registrado, com motivo.
        sa.CheckConstraint(
            "status <> 'REFUSED' OR (refused_at IS NOT NULL AND refused_by IS NOT NULL"
            " AND refusal_reason IS NOT NULL)",
            name="ck_payment_refused_requires_reason",
        ),
        # Exatamente uma origem. `guest_week_id` entra nesta conta quando a
        # tabela existir, na sprint do guest.
        sa.CheckConstraint(
            "(booking_id IS NOT NULL)::int + (session_id IS NOT NULL)::int = 1",
            name="ck_payment_single_origin",
        ),
        # O sinal pertence ao agendamento (RN-PAG-001): e o horario reservado que
        # ele confirma, e e por agendamento que a RN-AGE-005 exige o portao.
        sa.CheckConstraint(
            "kind <> 'DEPOSIT' OR booking_id IS NOT NULL",
            name="ck_payment_deposit_belongs_to_booking",
        ),
        # Reter e diferente de devolver: o estudio ficou com o dinheiro. Por isso
        # so um pagamento confirmado pode ser retido.
        sa.CheckConstraint(
            "retained_at IS NULL OR status = 'CONFIRMED'",
            name="ck_payment_retained_requires_confirmed",
        ),
        sa.CheckConstraint(
            "(retained_at IS NULL) = (retained_reason IS NULL)",
            name="ck_payment_retained_requires_reason",
        ),
    )
    op.create_index("ix_payment_booking_id", "payment", ["booking_id"])
    op.create_index("ix_payment_session_id", "payment", ["session_id"])
    op.create_index("ix_payment_status", "payment", ["status"])

    # RN-PAG-001: um sinal vivo por agendamento. Recusado permite outro; retido
    # tambem, porque a RN-AGE-008 manda o cliente pagar um novo depois de
    # remarcar fora do prazo.
    op.create_index(
        "uq_payment_live_deposit",
        "payment",
        ["booking_id"],
        unique=True,
        postgresql_where=sa.text(
            "kind = 'DEPOSIT' AND retained_at IS NULL"
            " AND status IN ('REPORTED', 'CONFIRMED')"
        ),
    )

    op.create_table(
        "payment_refund",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payment.id"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        # RN-PAG-009: a forma de devolucao pode diferir da forma original.
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("receipt_object_key", sa.Text(), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("amount > 0", name="ck_payment_refund_amount_positive"),
        sa.CheckConstraint(
            "method IN ('BANK_TRANSFER', 'CASH', 'CARD')",
            name="ck_payment_refund_method",
        ),
    )
    op.create_index("ix_payment_refund_payment_id", "payment_refund", ["payment_id"])


def downgrade() -> None:
    op.drop_table("payment_refund")
    op.drop_index("uq_payment_live_deposit", table_name="payment")
    op.drop_table("payment")
