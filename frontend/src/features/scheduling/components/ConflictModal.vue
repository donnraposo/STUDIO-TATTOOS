<script setup lang="ts">
import AppButton from "@/shared/components/AppButton.vue";
import AppModal from "@/shared/components/AppModal.vue";
import type { Booking } from "@/shared/domain/Booking";

/** O modal da RN-AGE-007.
 *
 * **Não existe caminho para ignorar o conflito, e isso é a regra e não uma
 * escolha de estilo.** Não há botão "criar assim mesmo", não fecha clicando no
 * fundo e não fecha com Esc. A única saída é reconhecer e voltar para escolher
 * outro horário.
 *
 * Isso não é rigor decorativo: a restrição `EXCLUDE` do banco recusaria a
 * gravação de qualquer forma (ADR-011). Um botão de ignorar produziria um erro
 * incompreensível em vez de uma explicação — e ensinaria a equipe a tentar de
 * novo esperando que desse certo.
 *
 * Os dois escopos dizem coisas diferentes e por isso têm textos diferentes: a
 * maca está ocupada, ou o artista já está comprometido em outro lugar
 * (RN-AGE-014). */
const SCOPE_EXPLANATION: Record<string, string> = {
  bench: "This bench is already taken for that period.",
  artist: "This artist is already committed in that period, in this or another bench.",
};

defineProps<{
  scope: string;
  message: string;
  existing: Booking | null;
  existingLabel: string | null;
}>();

defineEmits<{ acknowledge: [] }>();
</script>

<template>
  <AppModal
    title="Schedule conflict"
    :dismissible="false"
    @close="() => undefined"
  >
    <p class="explanation">
      {{ SCOPE_EXPLANATION[scope] ?? message }}
    </p>

    <div
      v-if="existing && existingLabel"
      class="existing"
    >
      <span class="label">Already booked</span>
      <strong>{{ existingLabel }}</strong>
    </div>
    <p
      v-else
      class="unknown"
    >
      The existing booking is not visible to you, but the period is taken.
    </p>

    <p class="rule">
      Pick another time or bench. The conflict cannot be overridden.
    </p>

    <template #actions>
      <AppButton @click="$emit('acknowledge')">
        Choose another time
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.explanation {
  font-size: var(--text-label-1);
}

.existing {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.label {
  font-size: var(--text-kicker);
  letter-spacing: var(--tracking-kicker);
  text-transform: uppercase;
}

.unknown,
.rule {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
