<script setup lang="ts">
import { PaymentDisplay } from "@/features/payments/PaymentDisplay";
import { PaymentTransitions } from "@/features/payments/PaymentTransitions";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Payment } from "@/shared/domain/Payment";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";
import { StudioClock } from "@/shared/format/StudioClock";

/** Os recebimentos do estúdio, com o que ainda se pode decidir em cada um
 * (RN-PAG-007).
 *
 * O nome do cliente chega pronto, por `props`: cruzar identificadores é
 * trabalho da tela, e assim este componente continua sem conhecer a API.
 *
 * **Um sinal retido é mostrado como tal, e não como confirmado e nada mais.**
 * O estúdio ficou com ele porque o horário foi reservado e perdido
 * (RN-AGE-009); quem lesse apenas "Confirmed" procuraria a devolução que nunca
 * houve.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  payments: Payment[];
  clientNames: Record<string, string>;
  canDecide: boolean;
  busy: boolean;
}>();

defineEmits<{
  confirm: [payment: Payment];
  refuse: [payment: Payment];
  refund: [payment: Payment];
}>();

const display = new PaymentDisplay();
const transitions = new PaymentTransitions();
const money = new MoneyFormatter();
const clock = new StudioClock();
</script>

<template>
  <ul class="list">
    <li
      v-for="payment in props.payments"
      :key="payment.id"
    >
      <AppCard>
        <template #header>
          <div class="who">
            <strong>{{ money.amount(payment.amount) }}</strong>
            <small>
              {{ display.kind(payment.kind) }} ·
              {{ payment.clientId ? (props.clientNames[payment.clientId] ?? "Client") : "Studio" }}
            </small>
          </div>
          <StatusBadge
            :label="display.status(payment.status).label"
            :tone="display.status(payment.status).tone"
          />
        </template>

        <dl class="facts">
          <div>
            <dt>Method</dt>
            <dd>{{ display.method(payment.method) }}</dd>
          </div>
          <div>
            <dt>Reported</dt>
            <dd>{{ clock.dateTime(payment.reportedAt) }}</dd>
          </div>
          <div v-if="payment.confirmedAt">
            <dt>Confirmed</dt>
            <dd>{{ clock.dateTime(payment.confirmedAt) }}</dd>
          </div>
          <div v-if="payment.refusalReason">
            <dt>Refused because</dt>
            <dd>{{ payment.refusalReason }}</dd>
          </div>
          <div v-if="display.isRetained(payment)">
            <dt>Kept by the studio</dt>
            <dd>{{ payment.retainedReason ?? "The booking was lost" }}</dd>
          </div>
          <div v-if="payment.note">
            <dt>Note</dt>
            <dd>{{ payment.note }}</dd>
          </div>
        </dl>

        <template
          v-if="props.canDecide && !transitions.isFinal(payment.status)"
          #footer
        >
          <AppButton
            v-if="transitions.canRefuse(payment.status)"
            tone="ghost"
            @click="$emit('refuse', payment)"
          >
            Refuse
          </AppButton>
          <AppButton
            v-if="transitions.canConfirm(payment.status)"
            :busy="props.busy"
            @click="$emit('confirm', payment)"
          >
            Confirm receipt
          </AppButton>
          <AppButton
            v-if="transitions.canRefund(payment.status)"
            tone="ghost"
            @click="$emit('refund', payment)"
          >
            Record refund
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
  font-size: var(--text-heading-3);
  font-weight: var(--weight-medium);
}

.who small {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.facts {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: var(--space-0);
}

dt {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

dd {
  margin: var(--space-0);
  overflow-wrap: anywhere;
}
</style>
