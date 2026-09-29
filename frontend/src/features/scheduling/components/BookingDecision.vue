<script setup lang="ts">
import { ref } from "vue";

import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Booking, RejectionReason } from "@/shared/domain/Booking";

/** Decisão sobre uma solicitação: aprovar ou recusar (RN-AGE-005, RN-AGE-006).
 *
 * **O motivo da recusa é lista fechada, e por isso é um seletor e não um campo
 * de texto.** A lista alimenta o tratamento financeiro do sinal e os relatórios
 * de cancelamento; texto livre tornaria os dois inúteis. A observação, essa
 * sim, é livre e opcional.
 *
 * O componente não decide quem pode decidir: recebe `canDecide` pronto. E o que
 * ele mostra é aparência — o backend recusa com 403 de qualquer forma. */
const REASONS: { value: RejectionReason; label: string }[] = [
  { value: "SLOT_TAKEN", label: "Slot already taken" },
  { value: "STUDIO_CLOSED", label: "Studio closed" },
  { value: "RESCHEDULED", label: "Rescheduled" },
];

defineProps<{
  booking: Booking;
  clientName: string;
  timeRange: string;
  canDecide: boolean;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{
  approve: [];
  reject: [reason: RejectionReason, note: string | null];
  close: [];
}>();

const rejecting = ref(false);
const reason = ref<RejectionReason>("SLOT_TAKEN");
const note = ref("");

function confirmRejection(): void {
  emit("reject", reason.value, note.value.trim() === "" ? null : note.value);
}
</script>

<template>
  <AppModal
    title="Booking"
    @close="$emit('close')"
  >
    <div class="summary">
      <strong>{{ clientName }}</strong>
      <span class="when">{{ timeRange }}</span>
      <StatusBadge
        :label="booking.status"
        :tone="booking.status === 'APPROVED' ? 'positive' : 'warning'"
      />
    </div>

    <template v-if="rejecting">
      <label class="field">
        <span>Reason</span>
        <select v-model="reason">
          <option
            v-for="option in REASONS"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </label>
      <AppInput
        v-model="note"
        label="Note (optional)"
        :disabled="busy"
      />
    </template>

    <p
      v-if="failure"
      class="failure"
      role="alert"
    >
      {{ failure }}
    </p>

    <template #actions>
      <template v-if="canDecide && booking.status === 'REQUESTED'">
        <AppButton
          tone="ghost"
          :disabled="busy"
          @click="rejecting ? (rejecting = false) : $emit('close')"
        >
          {{ rejecting ? "Back" : "Close" }}
        </AppButton>
        <AppButton
          v-if="!rejecting"
          tone="danger"
          :disabled="busy"
          @click="rejecting = true"
        >
          Reject
        </AppButton>
        <AppButton
          v-if="rejecting"
          tone="danger"
          :busy="busy"
          @click="confirmRejection"
        >
          Confirm rejection
        </AppButton>
        <AppButton
          v-if="!rejecting"
          :busy="busy"
          @click="$emit('approve')"
        >
          Approve
        </AppButton>
      </template>
      <AppButton
        v-else
        tone="ghost"
        @click="$emit('close')"
      >
        Close
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.summary {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.when {
  color: var(--color-muted);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field span {
  color: var(--color-muted);
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
}

select {
  min-height: var(--touch-target);
  padding: var(--space-2) var(--space-5);
  border: var(--border-thin);
  border-color: transparent;
  border-radius: var(--radius-round);
  background: var(--color-field);
  color: var(--color-on-light);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
