<script setup lang="ts">
import { computed, ref } from "vue";

import { PaymentDisplay } from "@/features/payments/PaymentDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import AppTextarea from "@/shared/components/AppTextarea.vue";
import type { Payment, PaymentMethod } from "@/shared/domain/Payment";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Registro de uma devolução **já realizada** (RN-PAG-009 e ADR-029).
 *
 * **Este botão não devolve dinheiro.** O gestor devolve por fora e lança aqui,
 * como em todo o resto do sistema nesta versão (RN-PAG-006). A tela diz isso
 * com todas as letras: quem opera dinheiro não deve precisar deduzir se um
 * botão movimenta caixa.
 *
 * **A forma é da devolução, não herdada do pagamento.** Um depósito devolvido
 * em dinheiro é caso previsto pela regra, e por isso o campo começa na forma
 * original apenas como sugestão.
 *
 * **O valor pode ser menor que o recebido**, e é o caso comum: quando o
 * atendimento é cancelado ou não comparecido, o estúdio retém o sinal e devolve o
 * restante (RN-PAG-004 e RN-AGE-009). Devolver mais do que entrou é recusado
 * pelo servidor, que soma as devoluções anteriores — conta que esta tela não
 * tem como fazer sozinha.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
export interface RefundDraft {
  amount: string;
  method: PaymentMethod;
  reason: string;
  note: string | null;
}

const props = defineProps<{
  payment: Payment;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ confirm: [refund: RefundDraft]; close: [] }>();

const METHOD_OPTIONS: SelectOption[] = [
  { value: "BANK_TRANSFER", label: "Bank transfer" },
  { value: "CASH", label: "Cash" },
  { value: "CARD", label: "Card" },
];

const display = new PaymentDisplay();
const money = new MoneyFormatter();

const amount = ref(props.payment.amount);
const method = ref<string>(props.payment.method);
const reason = ref("");
const note = ref("");

const ready = computed(
  () => amount.value.trim() !== "" && Number(amount.value) > 0 && reason.value.trim().length >= 3,
);

function refund(): void {
  if (ready.value) {
    emit("confirm", {
      amount: amount.value.trim(),
      method: method.value as PaymentMethod,
      reason: reason.value.trim(),
      note: note.value.trim() === "" ? null : note.value.trim(),
    });
  }
}
</script>

<template>
  <AppModal
    title="Record a refund"
    @close="$emit('close')"
  >
    <div class="summary">
      <strong>{{ money.amount(props.payment.amount) }}</strong>
      <span class="what">
        received as {{ display.kind(props.payment.kind).toLowerCase() }} by
        {{ display.method(props.payment.method).toLowerCase() }}
      </span>
    </div>

    <p class="notice">
      This records a refund you have already made. The studio does not move any
      money from here.
    </p>

    <form
      class="form"
      @submit.prevent="refund"
    >
      <AppInput
        v-model="amount"
        label="Amount returned"
        type="number"
        required
        :disabled="props.busy"
      />
      <AppSelect
        v-model="method"
        label="How it was returned"
        :options="METHOD_OPTIONS"
        required
        :disabled="props.busy"
      />
      <AppTextarea
        v-model="reason"
        label="Reason"
        placeholder="Why the money went back"
        required
        :disabled="props.busy"
      />
      <AppTextarea
        v-model="note"
        label="Note"
        :rows="2"
        :disabled="props.busy"
      />

      <p class="hint">
        Return less than the full amount when the studio keeps part of it — a
        lost booking keeps the deposit.
      </p>

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
        :disabled="!ready"
        :busy="props.busy"
        @click="refund"
      >
        Record refund
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
.hint {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

/* O aviso de que nada se movimenta em superfície própria: lido como parágrafo
   cinza, passaria batido justamente por quem opera dinheiro. */
.notice {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-info-soft);
  color: var(--color-on-light);
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
