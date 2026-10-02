<script setup lang="ts">
import { PayoutDisplay } from "@/features/payouts/PayoutDisplay";
import { PayoutWeekLabel } from "@/features/payouts/PayoutWeekLabel";
import AppButton from "@/shared/components/AppButton.vue";
import AppModal from "@/shared/components/AppModal.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { PayoutStatement } from "@/shared/domain/Payout";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** O demonstrativo do repasse (RN-REP-007).
 *
 * A regra lista o que ele exibe: "sessões incluídas, valor recebido por sessão,
 * percentual aplicado, ajustes positivos ou negativos e total líquido". Está
 * tudo aqui, e nessa ordem, porque é a ordem em que a conta se refaz — o artista
 * confere linha por linha contra o próprio extrato.
 *
 * **O percentual aparece em cada linha, e não uma vez no topo.** Ele é congelado
 * por sessão (RN-REP-006), e sessões de semanas diferentes podem ter percentuais
 * diferentes no mesmo repasse. Um número único no cabeçalho seria mentira na
 * primeira vez que isso acontecesse.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  statement: PayoutStatement;
  artistName: string;
  canConfirm: boolean;
  busy: boolean;
  failure: string | null;
}>();

defineEmits<{ confirm: []; close: [] }>();

const display = new PayoutDisplay();
const week = new PayoutWeekLabel();
const money = new MoneyFormatter();
</script>

<template>
  <AppModal
    title="Payout statement"
    @close="$emit('close')"
  >
    <div class="summary">
      <strong>{{ props.artistName }}</strong>
      <span class="when">
        {{ week.of(props.statement.payout.periodStart, props.statement.payout.periodEnd) }}
      </span>
      <StatusBadge
        :label="display.status(props.statement.payout.status).label"
        :tone="display.status(props.statement.payout.status).tone"
      />
    </div>

    <p class="closing">
      Week closed {{ week.closing(props.statement.payout.periodEnd) }}
    </p>

    <EmptyState
      v-if="props.statement.items.length === 0"
      title="No sessions in this week"
      description="Nothing was settled between the two Friday closings."
    />

    <table v-else>
      <thead>
        <tr>
          <th scope="col">
            Received
          </th>
          <th scope="col">
            Share
          </th>
          <th scope="col">
            Amount
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in props.statement.items"
          :key="item.id"
        >
          <td>{{ money.amount(item.receivedAmount) }}</td>
          <td>{{ money.percentage(item.percentage) }}</td>
          <td>{{ money.amount(item.amount) }}</td>
        </tr>
      </tbody>
    </table>

    <template v-if="props.statement.adjustments.length > 0">
      <h3>Adjustments</h3>
      <ul class="adjustments">
        <li
          v-for="adjustment in props.statement.adjustments"
          :key="adjustment.id"
        >
          <span>{{ money.amount(adjustment.amount) }}</span>
          <small>{{ adjustment.reason }}</small>
        </li>
      </ul>
    </template>

    <p class="net">
      <span>Net total</span>
      <strong>{{ money.amount(props.statement.payout.netTotal) }}</strong>
    </p>

    <p
      v-if="props.failure"
      class="failure"
      role="alert"
    >
      {{ props.failure }}
    </p>

    <template #actions>
      <AppButton
        tone="ghost"
        @click="$emit('close')"
      >
        Close
      </AppButton>
      <AppButton
        v-if="props.canConfirm && props.statement.payout.status !== 'PAID'"
        :busy="props.busy"
        @click="$emit('confirm')"
      >
        Confirm transfer
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
}

.when,
.closing {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: var(--space-3) var(--space-0);
  border-bottom: var(--border-thin);
  text-align: right;
}

th:first-child,
td:first-child {
  text-align: left;
}

th {
  color: var(--color-muted);
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
}

h3 {
  font-size: var(--text-label-1);
}

.adjustments {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

.adjustments li {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-3);
  color: var(--color-danger);
}

.adjustments small {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

/* O líquido fecha o demonstrativo em destaque: é o número que o artista
   confere contra o extrato. */
.net {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
  padding-top: var(--space-4);
  border-top: var(--border-thin);
}

.net strong {
  font-size: var(--text-heading-3);
  font-weight: var(--weight-medium);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
