<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { QuoteDisplay } from "@/features/quotes/QuoteDisplay";
import ReferenceImages from "@/features/quotes/components/ReferenceImages.vue";
import SessionList from "@/features/quotes/components/SessionList.vue";
import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppTextarea from "@/shared/components/AppTextarea.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Quote, ReferenceImage } from "@/shared/domain/Quote";
import type { TattooSession } from "@/shared/domain/TattooSession";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** O orçamento inteiro, com as decisões que cabem a quem está olhando.
 *
 * Aprovar e rejeitar são do gestor (RN-ORC-002); editar é do gestor sempre e do
 * artista enquanto o orçamento estiver pendente (RN-ORC-003). Esconder o botão
 * é cortesia — quem chegar pela API mesmo assim recebe 403.
 *
 * **A aprovação mostra o percentual antes de congelá-lo** (RN-REP-006). O campo
 * de correção fica vazio por padrão e, vazio, mantém o padrão da origem; é a
 * correção pontual que a RN-CLI-003 permite, e ela precisa ser um ato
 * deliberado, não o estado inicial do formulário.
 *
 * O modo corrente vem de um mapa de estados simples, como no modal de
 * agendamento: cada ação nova é uma entrada, não uma cadeia de `v-if` a mais. */
type Mode = "view" | "approve" | "reject";

const props = defineProps<{
  quote: Quote;
  clientName: string;
  artistName: string;
  createdAt: string;
  decidedAt: string | null;
  images: ReferenceImage[];
  sessions: TattooSession[];
  canMarkSessions: boolean;
  canDecide: boolean;
  canEdit: boolean;
  busy: boolean;
  failure: string | null;
  imagesBusy: boolean;
  imagesFailure: string | null;
}>();

const emit = defineEmits<{
  edit: [];
  approve: [artistPercentage: string | null];
  reject: [reason: string, note: string | null];
  markSession: [session: TattooSession];
  confirmSession: [session: TattooSession];
  attach: [file: File];
  remove: [imageId: string];
  close: [];
}>();

const display = new QuoteDisplay();
const money = new MoneyFormatter();

const mode = ref<Mode>("view");
const percentageOverride = ref("");
const rejectionReason = ref("");
const rejectionNote = ref("");

const look = computed(() => display.status(props.quote.status));
const isPending = computed(() => props.quote.status === "PENDING");

const standard = computed(() => display.standardPercentage(props.quote.origin));

/** O que será congelado se a aprovação seguir como está. */
const percentageNote = computed(() =>
  percentageOverride.value.trim() === ""
    ? `Freezes the studio standard for this origin: ${standard.value}% to the artist.`
    : `Freezes ${percentageOverride.value.trim()}% for this quote only, instead of the ${standard.value}% standard.`,
);

/** Decidido o orçamento, o modal volta à leitura.
 *
 * Sem isto, aprovar deixava na tela o campo de percentual e o botão "Confirm
 * approval" sobre um orçamento que já estava aprovado — e o segundo clique
 * voltava do servidor com "Only a pending quote can be approved.". Quem tinha
 * acabado de aprovar lia aquilo como falha da própria aprovação.
 *
 * Observa o estado e não o identificador porque é o estado que muda debaixo do
 * modal aberto: a tela recarrega e devolve o mesmo orçamento, decidido. */
watch(
  () => props.quote.status,
  () => {
    mode.value = "view";
    percentageOverride.value = "";
    rejectionReason.value = "";
    rejectionNote.value = "";
  },
);

const facts = computed(() => [
  { label: "Client", value: props.clientName },
  { label: "Artist", value: props.artistName },
  { label: "Origin", value: display.origin(props.quote.origin) },
  { label: "Body region", value: props.quote.bodyRegion },
  { label: "Estimated size", value: props.quote.sizeEstimate },
  { label: "Total value", value: money.amount(props.quote.totalValue) },
  { label: "Planned sessions", value: String(props.quote.plannedSessions) },
  { label: "Value per session", value: money.amount(props.quote.plannedValuePerSession) },
  { label: "Minutes per session", value: String(props.quote.estimatedDurationMinutes) },
  { label: "Created", value: props.createdAt },
]);
</script>

<template>
  <AppModal
    title="Quote"
    @close="$emit('close')"
  >
    <div class="summary">
      <strong>{{ props.clientName }}</strong>
      <StatusBadge
        :label="look.label"
        :tone="look.tone"
      />
    </div>

    <dl class="facts">
      <div
        v-for="fact in facts"
        :key="fact.label"
      >
        <dt>{{ fact.label }}</dt>
        <dd>{{ fact.value }}</dd>
      </div>
    </dl>

    <p class="description">
      {{ props.quote.description }}
    </p>

    <p
      v-if="props.quote.notes"
      class="notes"
    >
      {{ props.quote.notes }}
    </p>

    <!-- A decisão registrada, como manda a RN-ORC-002: o que foi decidido,
         quando, e com que acordo. -->
    <p
      v-if="props.quote.status === 'APPROVED'"
      class="decision is-approved"
    >
      Approved {{ props.decidedAt }} · artist share frozen at
      {{ money.percentage(props.quote.artistPercentage) }}
    </p>

    <p
      v-else-if="props.quote.status === 'REJECTED'"
      class="decision is-rejected"
    >
      Rejected: {{ props.quote.rejectionReason }}
      <template v-if="props.quote.rejectionNote">
        — {{ props.quote.rejectionNote }}
      </template>
    </p>

    <SessionList
      :sessions="props.sessions"
      :can-mark="props.canMarkSessions"
      :can-confirm="props.canDecide"
      :busy="props.busy"
      @mark="$emit('markSession', $event)"
      @confirm="$emit('confirmSession', $event)"
    />

    <ReferenceImages
      :images="props.images"
      :can-edit="props.canEdit"
      :busy="props.imagesBusy"
      :failure="props.imagesFailure"
      @attach="$emit('attach', $event)"
      @remove="$emit('remove', $event)"
    />

    <template v-if="mode === 'approve'">
      <AppInput
        v-model="percentageOverride"
        label="Artist share (optional)"
        type="number"
        :placeholder="standard"
        :disabled="props.busy"
      />
      <p class="freeze">
        {{ percentageNote }}
      </p>
    </template>

    <template v-if="mode === 'reject'">
      <AppInput
        v-model="rejectionReason"
        label="Reason"
        :disabled="props.busy"
        required
      />
      <AppTextarea
        v-model="rejectionNote"
        label="Note (optional)"
        :rows="3"
        :disabled="props.busy"
      />
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

        <AppButton
          v-if="props.canEdit"
          tone="ghost"
          :disabled="props.busy"
          @click="$emit('edit')"
        >
          Edit
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
            :disabled="props.busy"
            @click="mode = 'approve'"
          >
            Approve
          </AppButton>
        </template>
      </template>

      <template v-else>
        <AppButton
          tone="ghost"
          :disabled="props.busy"
          @click="mode = 'view'"
        >
          Back
        </AppButton>

        <AppButton
          v-if="mode === 'approve'"
          :busy="props.busy"
          @click="
            emit(
              'approve',
              percentageOverride.trim() === '' ? null : percentageOverride.trim(),
            )
          "
        >
          Confirm approval
        </AppButton>

        <AppButton
          v-if="mode === 'reject'"
          tone="danger"
          :busy="props.busy"
          :disabled="rejectionReason.trim().length < 3"
          @click="
            emit(
              'reject',
              rejectionReason.trim(),
              rejectionNote.trim() === '' ? null : rejectionNote.trim(),
            )
          "
        >
          Confirm rejection
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

.facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(var(--track-tile-min), 1fr));
  gap: var(--space-4);
  margin: var(--space-0);
}

dt {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

dd {
  margin: var(--space-0);
}

.description {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
  white-space: pre-wrap;
}

.notes {
  color: var(--color-muted);
  font-size: var(--text-label-3);
  white-space: pre-wrap;
}

.decision {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-label-3);
}

.is-approved {
  background: var(--color-positive-soft);
  color: var(--color-positive);
}

.is-rejected {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.freeze {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
