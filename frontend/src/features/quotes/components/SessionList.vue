<script setup lang="ts">
import { SessionDisplay } from "@/features/quotes/SessionDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { TattooSession } from "@/shared/domain/TattooSession";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";
import { StudioClock } from "@/shared/format/StudioClock";

/** As sessões de um orçamento aprovado (RN-ORC-005 e RN-ORC-006).
 *
 * **Mostra o previsto e o cobrado lado a lado**, e não só um deles. Numa sessão
 * parcial os dois divergem, e é dessa diferença que nasce o repasse menor
 * (RN-ORC-006) — esconder um dos números faria o artista descobrir a diferença
 * no fechamento de sexta.
 *
 * As duas ações são de gente diferente: o artista registra que aconteceu, o
 * gestor confirma quanto entrou. Esconder a que não cabe a quem olha é cortesia;
 * quem recusa de verdade é o backend, com 403.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  sessions: TattooSession[];
  canMark: boolean;
  canConfirm: boolean;
  busy: boolean;
}>();

defineEmits<{ mark: [session: TattooSession]; confirm: [session: TattooSession] }>();

const display = new SessionDisplay();
const money = new MoneyFormatter();
const clock = new StudioClock();
</script>

<template>
  <section class="sessions">
    <SectionKicker label="Sessions" />

    <p
      v-if="props.sessions.length === 0"
      class="none"
    >
      Sessions appear once the quote is approved.
    </p>

    <ul v-else>
      <li
        v-for="session in props.sessions"
        :key="session.id"
      >
        <span class="number">#{{ session.sequenceNumber }}</span>

        <StatusBadge
          :label="display.status(session.status).label"
          :tone="display.status(session.status).tone"
        />

        <span class="values">
          <strong>{{ money.amount(session.chargedValue ?? session.plannedValue) }}</strong>
          <small v-if="session.chargedValue && session.chargedValue !== session.plannedValue">
            of {{ money.amount(session.plannedValue) }} planned
          </small>
          <small v-else-if="session.performedAt">
            {{ clock.date(session.performedAt) }}
          </small>
        </span>

        <AppButton
          v-if="props.canMark && display.canMarkPerformed(session.status)"
          tone="ghost"
          :disabled="props.busy"
          @click="$emit('mark', session)"
        >
          {{ session.status === "SCHEDULED" ? "Mark performed" : "Correct" }}
        </AppButton>

        <AppButton
          v-if="props.canConfirm && display.canConfirmPayment(session.status)"
          :disabled="props.busy"
          @click="$emit('confirm', session)"
        >
          Confirm receipt
        </AppButton>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.sessions {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.none {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

ul {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
}

.number {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.values {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.values strong {
  font-weight: var(--weight-medium);
}

.values small {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

/* No celular a linha vira bloco: o número, o selo e dois botões em 375px
   deixam cada alvo pequeno demais para o polegar. */
@media (max-width: 40rem) {
  li {
    align-items: stretch;
  }

  .values {
    flex: 1 1 100%;
  }
}
</style>
