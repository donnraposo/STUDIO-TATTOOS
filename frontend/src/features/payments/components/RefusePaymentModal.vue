<script setup lang="ts">
import { computed, ref } from "vue";

import { PaymentDisplay } from "@/features/payments/PaymentDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppTextarea from "@/shared/components/AppTextarea.vue";
import type { Payment } from "@/shared/domain/Payment";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Recusa de um recebimento informado (RN-PAG-007).
 *
 * **O motivo é obrigatório**, e o botão fica travado sem ele. O lançamento
 * permanece no histórico, e um registro recusado sem explicação não diz a
 * ninguém por que o comprovante não valeu — nem ao cliente que vai perguntar.
 *
 * **Recusar não apaga nada e não tem volta.** O pagamento continua lá, agora
 * recusado, e não pode voltar a confirmado: a regra manda corrigir por
 * lançamento novo, não desfazendo o anterior. O texto diz isso, porque quem
 * clica esperando poder desfazer precisa saber antes.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  payment: Payment;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ confirm: [reason: string]; close: [] }>();

const display = new PaymentDisplay();
const money = new MoneyFormatter();

const reason = ref("");

const ready = computed(() => reason.value.trim().length >= 3);

function refuse(): void {
  if (ready.value) {
    emit("confirm", reason.value.trim());
  }
}
</script>

<template>
  <AppModal
    title="Refuse this payment"
    @close="$emit('close')"
  >
    <div class="summary">
      <strong>{{ money.amount(props.payment.amount) }}</strong>
      <span class="what">
        {{ display.kind(props.payment.kind) }} ·
        {{ display.method(props.payment.method) }}
      </span>
    </div>

    <p class="effect">
      The record stays in the history as refused. It cannot go back to
      confirmed — if the client pays again, that is a new payment.
    </p>

    <form
      class="form"
      @submit.prevent="refuse"
    >
      <AppTextarea
        v-model="reason"
        label="Reason"
        placeholder="Why the proof of payment was not accepted"
        required
        :disabled="props.busy"
      />

      <p
        v-if="props.failure"
        class="failure"
        role="alert"
      >
        {{ props.failure }}
      </p>
    </form>

    <template #actions>
      <AppButton
        tone="ghost"
        :disabled="props.busy"
        @click="$emit('close')"
      >
        Cancel
      </AppButton>
      <AppButton
        tone="danger"
        :disabled="!ready"
        :busy="props.busy"
        @click="refuse"
      >
        Refuse payment
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.summary {
  display: flex;
  flex-direction: column;
}

.summary strong {
  font-size: var(--text-heading-3);
  font-weight: var(--weight-medium);
}

.what,
.effect {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
