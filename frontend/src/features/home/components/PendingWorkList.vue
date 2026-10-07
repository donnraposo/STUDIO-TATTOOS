<script setup lang="ts">
import AppButton from "@/shared/components/AppButton.vue";
import StatusBadge, { type BadgeTone } from "@/shared/components/StatusBadge.vue";
import type { PendingWorkItem, PendingWorkKind } from "@/shared/domain/PendingWork";
import { StudioClock } from "@/shared/format/StudioClock";

/** O que está esperando decisão, numa lista só (RN-AGE-012 e seção 10.1).
 *
 * **Uma lista e não três.** Separar por origem obrigaria o gestor a olhar três
 * lugares — o mesmo problema que a área resolve, em escala menor. Juntas e
 * ordenadas por quem espera há mais tempo, a primeira linha é sempre a mais
 * urgente, venha de onde vier.
 *
 * O selo de origem diz de onde o item veio sem exigir leitura: agendamento,
 * pagamento ou orçamento. O tom vem de mapa tipado, não de cadeia de `v-if`.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. Não
 * navega nem decide — diz que o gestor escolheu um item, e a tela leva. */
const KIND: Record<PendingWorkKind, { label: string; tone: BadgeTone }> = {
  BOOKING: { label: "Booking", tone: "warning" },
  PAYMENT: { label: "Deposit", tone: "info" },
  QUOTE: { label: "Quote", tone: "neutral" },
};

const props = defineProps<{ items: PendingWorkItem[] }>();

defineEmits<{ open: [item: PendingWorkItem] }>();

const clock = new StudioClock();
</script>

<template>
  <ul class="pending">
    <li
      v-for="item in props.items"
      :key="`${item.kind}-${item.id}`"
    >
      <StatusBadge
        :label="KIND[item.kind].label"
        :tone="KIND[item.kind].tone"
      />

      <span class="what">
        <strong>{{ item.title }}</strong>
        <small>{{ item.detail }}</small>
      </span>

      <span class="since">{{ clock.dateTime(item.since) }}</span>

      <AppButton
        tone="ghost"
        @click="$emit('open', item)"
      >
        Open
      </AppButton>
    </li>
  </ul>
</template>

<style scoped>
.pending {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.what {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: var(--track-tile-min);
}

.what strong {
  font-weight: var(--weight-medium);
}

.what small,
.since {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

/* No celular o item vira bloco: quatro colunas em 375px deixam o nome do
   cliente com duas palavras por linha. A hora de entrada sai do fim da linha e
   passa a acompanhar o texto. */
@media (max-width: 40rem) {
  li {
    align-items: stretch;
    gap: var(--space-3);
  }

  .what {
    flex: 1 1 100%;
  }

  .since {
    flex: 1;
  }
}
</style>
