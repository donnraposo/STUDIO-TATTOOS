<script setup lang="ts">
import { computed, ref } from "vue";

import {
  BookingConsequence,
  type BookingDecisionKind,
} from "@/features/scheduling/BookingConsequence";
import AppButton from "@/shared/components/AppButton.vue";
import AppCheckbox from "@/shared/components/AppCheckbox.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Booking, Bench, RejectionReason } from "@/shared/domain/Booking";
import type { ClientContact } from "@/shared/domain/Client";

/** Decisão sobre um agendamento: aprovar, recusar, cancelar, marcar não
 * comparecimento ou remarcar.
 *
 * **Cada ação mostra o que faz com o dinheiro antes de ser confirmada.** As
 * regras tratam sinal de formas diferentes em cada caso — cancelar retém mesmo
 * com aviso, não comparecer retém e tira o repasse, remarcar depende das 24
 * horas — e o gestor não pode descobrir isso depois.
 *
 * O modo corrente vem de um mapa tipado, e não de uma cadeia de `v-if`: cada
 * ação nova é uma entrada de dados.
 *
 * **`requestedAt` é mostrado sempre.** A RN-AGE-004 manda exibir as
 * solicitações concorrentes com a data e a hora em que cada uma foi enviada —
 * é o critério que o gestor usa para escolher qual aprovar.
 *
 * **O sinal entra por `slot`.** Até a M7.2.3 o botão de aprovar levava 403
 * quando não havia recebimento confirmado, sem nada na tela que dissesse o quê
 * (RN-AGE-005). O painel do sinal passa a ficar aqui, onde a pergunta aparece —
 * mas por `slot`, para que este componente continue decidindo sobre horário e
 * não passe a conhecer pagamento. */
type Mode = "view" | "reject" | "cancel" | "reschedule";

const REJECTION_REASONS: SelectOption[] = [
  { value: "SLOT_TAKEN", label: "Slot already taken" },
  { value: "STUDIO_CLOSED", label: "Studio closed" },
  { value: "RESCHEDULED", label: "Rescheduled" },
];

const props = defineProps<{
  booking: Booking;
  clientName: string;
  /** Contato do cliente deste agendamento (RN-CLI-004).
   *
   * A regra diz que o artista a quem o estúdio encaminha um cliente vê **nome,
   * telefone e Instagram dentro do próprio agendamento** — é exatamente aqui.
   * Nulo enquanto carrega, ou quando o servidor não devolveu o cadastro. */
  clientContact: ClientContact | null;
  artistName: string;
  timeRange: string;
  requestedAt: string;
  benches: Bench[];
  canDecide: boolean;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{
  approve: [];
  reject: [reason: RejectionReason, note: string | null];
  cancel: [reason: string, noShow: boolean];
  reschedule: [startTime: string, endTime: string, benchId: string | null];
  close: [];
}>();

const consequences = new BookingConsequence();

const mode = ref<Mode>("view");
const rejectionReason = ref<string>("SLOT_TAKEN");
const rejectionNote = ref("");
const cancelReason = ref("");
const markAsNoShow = ref(false);
const newStart = ref("");
const newEnd = ref("");
const newBenchId = ref("");

const isPending = computed(() => props.booking.status === "REQUESTED");
const isApproved = computed(() => props.booking.status === "APPROVED");

const benchOptions = computed<SelectOption[]>(() => [
  ...props.benches.map((bench) => ({ value: bench.id, label: `Bench ${bench.number}` })),
]);

const consequence = computed(() => {
  const kind: BookingDecisionKind | null =
    mode.value === "reject"
      ? "reject"
      : mode.value === "cancel"
        ? markAsNoShow.value
          ? "noShow"
          : "cancel"
        : mode.value === "reschedule"
          ? "reschedule"
          : isPending.value
            ? "approve"
            : null;
  return kind ? consequences.describe(kind) : null;
});

const invalidPeriod = computed(
  () => newStart.value !== "" && newEnd.value !== "" && newEnd.value <= newStart.value,
);

function back(): void {
  mode.value = "view";
}
</script>

<template>
  <AppModal
    title="Booking"
    @close="$emit('close')"
  >
    <div class="summary">
      <strong>{{ props.clientName }}</strong>
      <span class="when">{{ props.timeRange }}</span>
      <StatusBadge
        :label="props.booking.status"
        :tone="isApproved ? 'positive' : 'warning'"
      />
    </div>

    <p class="requested">
      {{ props.artistName }} · requested {{ props.requestedAt }}
    </p>

    <!-- RN-CLI-004: nome, telefone e Instagram dentro do proprio agendamento.
         E o que permite ao artista saber quem vem sem abrir a ficha do
         cliente, que pode nem ser dele. -->
    <dl
      v-if="props.clientContact"
      class="contact"
    >
      <div>
        <dt>Phone</dt>
        <dd>{{ props.clientContact.phone }}</dd>
      </div>
      <div v-if="props.clientContact.instagram">
        <dt>Instagram</dt>
        <dd>{{ props.clientContact.instagram }}</dd>
      </div>
    </dl>

    <!-- O trabalho orçado e o sinal entram por `slot` e não por `props`: este
         componente decide sobre o horário e não precisa saber o que é um
         orçamento nem um pagamento. Quem monta os painéis é a tela, que é quem
         fala com a API. Só no modo de leitura — no meio de uma recusa ou de um
         remarcar, eles seriam ruído. -->
    <template v-if="mode === 'view'">
      <slot name="work" />
      <slot name="deposit" />
    </template>

    <p
      v-if="consequence"
      class="consequence"
    >
      {{ consequence }}
    </p>

    <template v-if="mode === 'reject'">
      <AppSelect
        v-model="rejectionReason"
        label="Reason"
        :options="REJECTION_REASONS"
        :disabled="props.busy"
        required
      />
      <AppInput
        v-model="rejectionNote"
        label="Note (optional)"
        :disabled="props.busy"
      />
    </template>

    <template v-if="mode === 'cancel'">
      <AppInput
        v-model="cancelReason"
        label="Reason"
        :disabled="props.busy"
        required
      />
      <AppCheckbox
        v-model="markAsNoShow"
        label="The client did not show up"
        :disabled="props.busy"
      />
    </template>

    <template v-if="mode === 'reschedule'">
      <AppSelect
        v-model="newBenchId"
        label="Bench"
        placeholder="Keep the same bench"
        :options="benchOptions"
        :disabled="props.busy"
      />
      <div class="period">
        <AppInput
          v-model="newStart"
          label="New start"
          type="time"
          :disabled="props.busy"
          required
        />
        <AppInput
          v-model="newEnd"
          label="New end"
          type="time"
          :error="invalidPeriod ? 'The end must be after the start.' : null"
          :disabled="props.busy"
          required
        />
      </div>
    </template>

    <p
      v-if="props.failure"
      class="failure"
      role="alert"
    >
      {{ props.failure }}
    </p>

    <template #actions>
      <template v-if="mode === 'view'">
        <AppButton
          tone="ghost"
          @click="$emit('close')"
        >
          Close
        </AppButton>

        <template v-if="props.canDecide && isPending">
          <AppButton
            tone="danger"
            :disabled="props.busy"
            @click="mode = 'reject'"
          >
            Reject
          </AppButton>
          <AppButton
            :busy="props.busy"
            @click="$emit('approve')"
          >
            Approve
          </AppButton>
        </template>

        <template v-if="props.canDecide && isApproved">
          <AppButton
            tone="ghost"
            :disabled="props.busy"
            @click="mode = 'reschedule'"
          >
            Reschedule
          </AppButton>
          <AppButton
            tone="danger"
            :disabled="props.busy"
            @click="mode = 'cancel'"
          >
            Cancel booking
          </AppButton>
        </template>
      </template>

      <template v-else>
        <AppButton
          tone="ghost"
          :disabled="props.busy"
          @click="back"
        >
          Back
        </AppButton>

        <AppButton
          v-if="mode === 'reject'"
          tone="danger"
          :busy="props.busy"
          @click="
            emit(
              'reject',
              rejectionReason as RejectionReason,
              rejectionNote.trim() === '' ? null : rejectionNote,
            )
          "
        >
          Confirm rejection
        </AppButton>

        <AppButton
          v-if="mode === 'cancel'"
          tone="danger"
          :busy="props.busy"
          :disabled="cancelReason.trim() === ''"
          @click="emit('cancel', cancelReason, markAsNoShow)"
        >
          {{ markAsNoShow ? "Mark as no-show" : "Confirm cancellation" }}
        </AppButton>

        <AppButton
          v-if="mode === 'reschedule'"
          :busy="props.busy"
          :disabled="newStart === '' || newEnd === '' || invalidPeriod"
          @click="emit('reschedule', newStart, newEnd, newBenchId === '' ? null : newBenchId)"
        >
          Move booking
        </AppButton>
      </template>
    </template>
  </AppModal>
</template>

<style scoped>
.summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
}

.when {
  color: var(--color-muted);
}

/* Contato em duas colunas: sao dois fatos curtos, e empilhados empurrariam o
   resto do modal para baixo sem necessidade. */
.contact {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  margin: var(--space-0);
}

.contact dt {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.contact dd {
  margin: var(--space-0);
  overflow-wrap: anywhere;
}

.requested {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

/* A consequência fica em destaque suave, e não como alerta: é informação que
   precede a decisão, não um erro que aconteceu. */
.consequence {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-warning-soft);
  color: var(--color-warning);
  font-size: var(--text-label-3);
}

.period {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}

@media (max-width: 40rem) {
  .period {
    grid-template-columns: 1fr;
  }
}
</style>
