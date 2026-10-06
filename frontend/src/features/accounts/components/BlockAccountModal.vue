<script setup lang="ts">
import { computed, ref } from "vue";

import { AccountDisplay } from "@/features/accounts/AccountDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppTextarea from "@/shared/components/AppTextarea.vue";
import type { StudioAccount } from "@/shared/domain/StudioAccount";

/** Bloqueio de conta, com o motivo que a RN 2.5 exige.
 *
 * **O motivo é obrigatório**, e o botão fica desabilitado sem ele. Bloquear sem
 * registrar por quê deixaria, meses depois, uma conta sem acesso e ninguém que
 * soubesse dizer o que aconteceu.
 *
 * **Não é exclusão.** O histórico, os pagamentos e os atendimentos continuam —
 * o que acaba é o acesso, e as sessões abertas são encerradas na hora. Os
 * agendamentos futuros ficam: cabe ao gestor transferi-los ou cancelá-los, e o
 * texto diz isso para que ele não descubra pela ausência do artista.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  account: StudioAccount;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ confirm: [reason: string]; close: [] }>();

const display = new AccountDisplay();

const reason = ref("");

const ready = computed(() => reason.value.trim() !== "");

function confirm(): void {
  if (ready.value) {
    emit("confirm", reason.value.trim());
  }
}
</script>

<template>
  <AppModal
    :title="`Block ${display.name(props.account)}`"
    @close="$emit('close')"
  >
    <p class="effect">
      They lose access immediately and any open session ends. Their history,
      payments and sessions stay. Bookings already in the calendar are not
      cancelled — move or cancel them yourself.
    </p>

    <form
      class="form"
      @submit.prevent="confirm"
    >
      <AppTextarea
        v-model="reason"
        label="Reason"
        placeholder="Why this account is being blocked"
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
        @click="confirm"
      >
        Block account
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
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
