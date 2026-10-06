<script setup lang="ts">
import { computed, ref } from "vue";

import { BookingDeposit } from "@/features/payments/BookingDeposit";
import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import AppTextarea from "@/shared/components/AppTextarea.vue";
import type { PaymentKind, PaymentMethod } from "@/shared/domain/Payment";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Lançamento de um recebimento informado (RN-PAG-002 e RN-PAG-006).
 *
 * **O valor do sinal não é digitado.** A RN-PAG-001 diz €50 por agendamento, e
 * um campo aberto convidaria a digitar outro valor — que o estúdio depois
 * descobriria no fechamento de sexta. O campo só aparece no pagamento integral
 * antecipado (RN-PAG-004), que é livre por definição.
 *
 * **Nasce aguardando confirmação, nunca confirmado.** Informar e confirmar são
 * atos diferentes: o comprovante chega, o gestor confere, e só então confirma.
 * O texto diz isso, porque quem lança esperando liberar o horário na hora
 * precisa saber que falta um passo.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
export interface PaymentDraft {
  amount: string;
  kind: PaymentKind;
  method: PaymentMethod;
  note: string | null;
}

const props = defineProps<{
  subject: string;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ submit: [draft: PaymentDraft]; close: [] }>();

const KIND_OPTIONS: SelectOption[] = [
  { value: "DEPOSIT", label: "Deposit" },
  { value: "FULL_PREPAY", label: "Full prepayment" },
];

const METHOD_OPTIONS: SelectOption[] = [
  { value: "BANK_TRANSFER", label: "Bank transfer" },
  { value: "CASH", label: "Cash" },
  { value: "CARD", label: "Card" },
];

const money = new MoneyFormatter();

const kind = ref<string>("DEPOSIT");
const amount = ref("");
const method = ref<string>("BANK_TRANSFER");
const note = ref("");

const isDeposit = computed(() => kind.value === "DEPOSIT");

const value = computed(() => (isDeposit.value ? BookingDeposit.AMOUNT : amount.value.trim()));

const ready = computed(() => value.value !== "" && Number(value.value) > 0);

function submit(): void {
  if (ready.value) {
    emit("submit", {
      amount: value.value,
      kind: kind.value as PaymentKind,
      method: method.value as PaymentMethod,
      note: note.value.trim() === "" ? null : note.value.trim(),
    });
  }
}
</script>

<template>
  <AppModal
    title="Register a payment"
    @close="$emit('close')"
  >
    <p class="subject">
      {{ props.subject }}
    </p>

    <form
      class="form"
      @submit.prevent="submit"
    >
      <AppSelect
        v-model="kind"
        label="What this covers"
        :options="KIND_OPTIONS"
        required
        :disabled="props.busy"
      />

      <p
        v-if="isDeposit"
        class="fixed"
      >
        <span>Amount</span>
        <strong>{{ money.amount(BookingDeposit.AMOUNT) }}</strong>
      </p>
      <AppInput
        v-else
        v-model="amount"
        label="Amount"
        type="number"
        required
        :disabled="props.busy"
      />

      <AppSelect
        v-model="method"
        label="How it was paid"
        :options="METHOD_OPTIONS"
        required
        :disabled="props.busy"
      />
      <AppTextarea
        v-model="note"
        label="Note"
        :rows="2"
        placeholder="Reference of the transfer, for example"
        :disabled="props.busy"
      />

      <p class="notice">
        This records that the money was reported. You still have to confirm the
        receipt before the booking can be approved.
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
        @click="submit"
      >
        Register payment
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.subject {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* O sinal tem valor fixo, e por isso aparece como fato e não como campo: um
   campo aberto convida a digitar outro valor. */
.fixed {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
}

.fixed span {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.fixed strong {
  font-weight: var(--weight-medium);
}

.notice {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-info-soft);
  color: var(--color-on-light);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
