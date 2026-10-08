<script setup lang="ts">
import { computed, ref, watch } from "vue";

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
 * **O valor do sinal chega preenchido e é editável.** Ele vem do que o artista
 * informou ao marcar o horário — cada um cobra o seu —, e quem registra pode
 * corrigi-lo: entre o combinado e o que entrou de verdade há a vida real, e é
 * o gestor quem vê o comprovante.
 *
 * Preenchido e não em branco porque o caminho comum é confirmar o que foi
 * combinado; um campo vazio obrigaria a redigitar o mesmo número toda vez. Sem
 * nada informado, cai no padrão do estúdio.
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
  /** O sinal informado ao marcar o horário. Nulo cai no padrão do estúdio. */
  expectedDeposit: string | null;
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

/** O sinal combinado para este horário, ou o padrão do estúdio quando quem
 * marcou não informou nenhum. Num lugar só: a inicialização e a troca de tipo
 * fazem a mesma pergunta, e duas cópias divergiriam no primeiro ajuste. */
function suggestedDeposit(): string {
  return props.expectedDeposit ?? BookingDeposit.AMOUNT;
}

const kind = ref<string>("DEPOSIT");
const amount = ref(suggestedDeposit());
const method = ref<string>("BANK_TRANSFER");
const note = ref("");

const isDeposit = computed(() => kind.value === "DEPOSIT");

const value = computed(() => amount.value.trim());

const ready = computed(() => value.value !== "" && Number(value.value) > 0);

/** Trocar o tipo troca o valor sugerido: o sinal tem um combinado, o pagamento
 * integral antecipado não tem nenhum. Sem isto, escolher "integral" deixaria o
 * valor do sinal no campo, e alguém registraria a tatuagem inteira por €50. */
watch(kind, (chosen) => {
  amount.value = chosen === "DEPOSIT" ? suggestedDeposit() : "";
});

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

      <AppInput
        v-model="amount"
        label="Amount (€)"
        type="number"
        required
        :disabled="props.busy"
      />
      <p
        v-if="isDeposit && props.expectedDeposit"
        class="hint"
      >
        The artist recorded {{ money.amount(props.expectedDeposit) }} for this
        booking. Change it if what arrived was different.
      </p>

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

.hint {
  color: var(--color-muted);
  font-size: var(--text-label-3);
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
