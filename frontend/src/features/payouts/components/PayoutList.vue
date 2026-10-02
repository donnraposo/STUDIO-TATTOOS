<script setup lang="ts">
import { PayoutDisplay } from "@/features/payouts/PayoutDisplay";
import { PayoutWeekLabel } from "@/features/payouts/PayoutWeekLabel";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Payout } from "@/shared/domain/Payout";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Os repasses visíveis a quem está olhando (RN-REP-004).
 *
 * **Não filtra nada.** O backend já devolve o recorte certo — o artista vê os
 * seus, o gestor vê todos. Repetir a regra aqui daria duas versões dela, e num
 * módulo que diz quanto cada pessoa recebeu essa divergência é a última que se
 * quer.
 *
 * O nome do artista chega pronto, por `props`: cruzar identificadores é
 * trabalho da tela, e assim este componente continua sem conhecer a API.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  payouts: Payout[];
  artistNames: Record<string, string>;
  canConfirm: boolean;
  busy: boolean;
}>();

defineEmits<{ open: [payout: Payout]; confirm: [payout: Payout] }>();

const display = new PayoutDisplay();
const week = new PayoutWeekLabel();
const money = new MoneyFormatter();
</script>

<template>
  <ul class="list">
    <li
      v-for="payout in props.payouts"
      :key="payout.id"
    >
      <AppCard>
        <template #header>
          <div class="who">
            <strong>{{ props.artistNames[payout.artistId] ?? "Artist" }}</strong>
            <small>{{ week.of(payout.periodStart, payout.periodEnd) }}</small>
          </div>
          <StatusBadge
            :label="display.status(payout.status).label"
            :tone="display.status(payout.status).tone"
          />
        </template>

        <dl class="numbers">
          <div>
            <dt>Sessions</dt>
            <dd>{{ money.amount(payout.grossTotal) }}</dd>
          </div>
          <div>
            <dt>Adjustments</dt>
            <dd>{{ money.amount(payout.adjustmentsTotal) }}</dd>
          </div>
          <div class="net">
            <dt>Net</dt>
            <dd>{{ money.amount(payout.netTotal) }}</dd>
          </div>
        </dl>

        <template #footer>
          <AppButton
            tone="ghost"
            @click="$emit('open', payout)"
          >
            Statement
          </AppButton>
          <AppButton
            v-if="props.canConfirm && payout.status !== 'PAID'"
            :busy="props.busy"
            @click="$emit('confirm', payout)"
          >
            Confirm transfer
          </AppButton>
        </template>
      </AppCard>
    </li>
  </ul>
</template>

<style scoped>
.list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--track-card-min), 1fr));
  gap: var(--space-4);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

.who {
  display: flex;
  flex-direction: column;
}

.who strong {
  font-weight: var(--weight-medium);
}

.who small {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.numbers {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
  margin: var(--space-0);
}

dt {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

dd {
  margin: var(--space-0);
}

/* O líquido é o número que o artista recebe, e precisa se destacar dos dois que
   o explicam. */
.net dd {
  font-weight: var(--weight-medium);
}

@media (max-width: 40rem) {
  .numbers {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
