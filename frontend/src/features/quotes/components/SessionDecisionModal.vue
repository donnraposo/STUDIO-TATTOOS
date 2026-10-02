<script setup lang="ts">
import { computed, ref } from "vue";

import AppButton from "@/shared/components/AppButton.vue";
import AppCheckbox from "@/shared/components/AppCheckbox.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppTextarea from "@/shared/components/AppTextarea.vue";
import type { TattooSession } from "@/shared/domain/TattooSession";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Registrar que a sessão aconteceu, ou confirmar quanto entrou.
 *
 * **Dois atos de gente diferente, no mesmo modal.** O artista marca a sessão
 * como realizada (RN-ORC-005); o gestor confirma o recebimento, e é a
 * confirmação que a libera para repasse. Separá-los em dois componentes
 * duplicaria o resumo da sessão e o campo de valor, que são os mesmos.
 *
 * **Parcial cobra menos que o previsto.** O servidor recusa valor igual ou
 * maior, porque aceitar o previsto marcaria como interrompida uma sessão que
 * correu inteira — e o repasse sairia certo por acaso enquanto o histórico
 * contaria outra coisa. A tela avisa antes de enviar.
 *
 * **Confirmar valor diferente do informado exige motivo** (RN-ORC-005):
 * correção silenciosa de valor é a diferença entre um acerto e um desvio, e sem
 * o motivo escrito nenhuma das duas se distingue da outra.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
type Mode = "mark" | "confirm";

const props = defineProps<{
  session: TattooSession;
  mode: Mode;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{
  mark: [chargedValue: string | null];
  confirm: [chargedValue: string | null, reason: string | null];
  close: [];
}>();

const money = new MoneyFormatter();

const partial = ref(props.session.status === "PARTIALLY_DONE");
const chargedValue = ref(props.session.chargedValue ?? "");
const reason = ref("");

const reported = computed(() => props.session.chargedValue ?? props.session.plannedValue);

/** Parcial precisa cobrar menos que o previsto, e o aviso vem antes do envio. */
const invalidPartial = computed(() => {
  if (!partial.value || chargedValue.value.trim() === "") {
    return false;
  }
  return Number(chargedValue.value) >= Number(props.session.plannedValue);
});

/** Mudar o valor na confirmação é correção, e correção pede motivo. */
const corrects = computed(
  () => props.mode === "confirm" && chargedValue.value.trim() !== "" &&
    Number(chargedValue.value) !== Number(reported.value),
);

const blocked = computed(() => {
  if (props.mode === "mark") {
    return invalidPartial.value || (partial.value && chargedValue.value.trim() === "");
  }
  return corrects.value && reason.value.trim() === "";
});

function submit(): void {
  if (props.mode === "mark") {
    emit("mark", partial.value ? chargedValue.value.trim() : null);
    return;
  }
  emit(
    "confirm",
    chargedValue.value.trim() === "" ? null : chargedValue.value.trim(),
    reason.value.trim() === "" ? null : reason.value.trim(),
  );
}
</script>

<template>
  <AppModal
    :title="props.mode === 'mark' ? 'Mark session as performed' : 'Confirm what came in'"
    @close="$emit('close')"
  >
    <p class="summary">
      Session #{{ props.session.sequenceNumber }} ·
      {{ money.amount(props.session.plannedValue) }} planned ·
      {{ money.percentage(props.session.artistPercentage) }} to the artist
    </p>

    <template v-if="props.mode === 'mark'">
      <AppCheckbox
        v-model="partial"
        label="The session was interrupted"
        :disabled="props.busy"
      />

      <AppInput
        v-if="partial"
        v-model="chargedValue"
        label="Amount actually charged (€)"
        type="number"
        :error="
          invalidPartial
            ? 'A partial session must be charged less than the planned value.'
            : null
        "
        :disabled="props.busy"
        required
      />

      <p class="note">
        Marking does not settle the session. The studio management confirms what
        came in, and only then it counts towards the payout.
      </p>
    </template>

    <template v-else>
      <AppInput
        v-model="chargedValue"
        label="Amount received (€)"
        type="number"
        :placeholder="reported"
        :disabled="props.busy"
      />

      <AppTextarea
        v-if="corrects"
        v-model="reason"
        label="Reason for the correction"
        :rows="3"
        :disabled="props.busy"
        required
      />

      <p class="note">
        This records that the studio received the money. It does not move
        anything — the payment happens outside the system.
      </p>
    </template>

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
        :disabled="props.busy"
        @click="$emit('close')"
      >
        Cancel
      </AppButton>
      <AppButton
        :busy="props.busy"
        :disabled="blocked"
        @click="submit"
      >
        {{ props.mode === "mark" ? "Record session" : "Confirm receipt" }}
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.summary {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

/* O que o ato faz e o que ele não faz, em tom de informação e não de alerta:
   precede a decisão, não relata falha. */
.note {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
