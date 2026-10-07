<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { QuoteDisplay } from "@/features/quotes/QuoteDisplay";
import { QuoteDraftCheck } from "@/features/quotes/QuoteDraftCheck";
import { QuoteOriginSuggestion } from "@/features/quotes/QuoteOriginSuggestion";
import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import AppTextarea from "@/shared/components/AppTextarea.vue";
import type { Client } from "@/shared/domain/Client";
import type { Quote, QuoteFields, QuoteOrigin } from "@/shared/domain/Quote";
import type { StudioMember } from "@/shared/domain/StudioMember";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Orçamento novo ou em edição (RN-ORC-003 e RN-ORC-004).
 *
 * **Editar um orçamento já decidido o devolve a Pendente**, e o aviso no topo
 * existe por isso. Quem abre o formulário para corrigir uma palavra na
 * descrição não espera perder a aprovação junto — e, no caso de um aprovado,
 * perder com ela o percentual congelado (RN-REP-006). Dizer isso depois de
 * salvar seria dizer tarde demais.
 *
 * **Cliente e artista só aparecem na criação.** Reatribuir um orçamento a outra
 * pessoa não é editar: é outro atendimento, e o backend ignora os dois campos
 * no `PUT`. Oferecê-los aqui prometeria algo que não acontece.
 *
 * Componente de apresentação: não conhece a API. Recebe listas por `props` e
 * devolve o rascunho por `emits`. */
export interface QuoteDraft {
  clientId: string;
  artistId: string | null;
  fields: QuoteFields;
}

const props = defineProps<{
  quote: Quote | null;
  /** Quem está orçando, para reconhecer "cliente próprio" quando o artista não
   * é escolhido explicitamente. */
  selfArtistId: string | null;
  clients: Client[];
  artists: StudioMember[];
  canChooseArtist: boolean;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ submit: [draft: QuoteDraft]; close: [] }>();

const display = new QuoteDisplay();
const check = new QuoteDraftCheck();
const suggestion = new QuoteOriginSuggestion();
const money = new MoneyFormatter();

const editing = props.quote;

const clientId = ref(editing?.clientId ?? "");
const artistId = ref(editing?.artistId ?? "");
/** Guardado como texto porque é o que `AppSelect` devolve, e lido como origem
 * num ponto só. A alternativa seria converter em cada uso, e cada conversão é
 * uma chance de esquecer uma. */
const origin = ref<string>(editing?.origin ?? "ARTIST_OWN");
const description = ref(editing?.description ?? "");
const bodyRegion = ref(editing?.bodyRegion ?? "");
const sizeEstimate = ref(editing?.sizeEstimate ?? "");
const totalValue = ref(editing?.totalValue ?? "");
const plannedSessions = ref(String(editing?.plannedSessions ?? 1));
const plannedValuePerSession = ref(editing?.plannedValuePerSession ?? "");
const estimatedDurationMinutes = ref(String(editing?.estimatedDurationMinutes ?? 120));
const notes = ref(editing?.notes ?? "");

const isEditing = computed(() => props.quote !== null);
const selectedOrigin = computed(() => origin.value as QuoteOrigin);

/** Escolher o cliente já marca a origem provável (RN-CLI-002).
 *
 * **Sugere e não prende:** o campo continua editável, porque a regra manda
 * determinar a origem em cada atendimento. O que a sugestão evita é o caminho
 * oposto — abrir sempre em "cliente próprio" e deixar que o descuido pague 70%
 * numa indicação do estúdio.
 *
 * Só na criação. Num orçamento existente a origem já foi decidida, e
 * sobrescrevê-la ao abrir o formulário apagaria uma decisão do gestor sem
 * ninguém pedir. */
watch([clientId, artistId], ([client, artist]) => {
  if (isEditing.value) {
    return;
  }
  const chosen = props.clients.find((candidate) => candidate.id === client) ?? null;
  origin.value = suggestion.for(chosen, artist === "" ? props.selfArtistId : artist);
});

const clientOptions = computed<SelectOption[]>(() =>
  props.clients.map((client) => ({ value: client.id, label: client.name })),
);

const artistOptions = computed<SelectOption[]>(() =>
  props.artists.map((artist) => ({ value: artist.id, label: artist.displayName })),
);

const originOptions = computed<SelectOption[]>(() =>
  display.origins().map((value) => ({ value, label: display.origin(value) })),
);

/** O que a origem escolhida vale hoje, para que a decisão seja informada antes
 * de existir. O número que valerá de verdade é o congelado na aprovação. */
const shareNote = computed(
  () =>
    `Studio standard for this origin: ${display.standardPercentage(
      selectedOrigin.value,
    )}% to the artist.`,
);

/** O aviso da RN-ORC-003, no tom que cada estado merece. Um aprovado perde mais
 * do que um rejeitado, e o texto precisa dizer o quê. */
const decisionWarning = computed(() => {
  const quote = props.quote;
  if (!quote || quote.status === "PENDING") {
    return null;
  }
  if (quote.status === "APPROVED") {
    return `Saving sends this quote back to Pending and discards the agreed ${money.percentage(
      quote.artistPercentage,
    )} share. It has to be approved again.`;
  }
  return "Saving sends this rejected quote back to Pending for a new decision.";
});

const report = computed(() =>
  check.review(
    {
      clientId: clientId.value,
      description: description.value,
      bodyRegion: bodyRegion.value,
      sizeEstimate: sizeEstimate.value,
      totalValue: totalValue.value,
      plannedSessions: plannedSessions.value,
      plannedValuePerSession: plannedValuePerSession.value,
      estimatedDurationMinutes: estimatedDurationMinutes.value,
      notes: notes.value,
    },
    !isEditing.value,
  ),
);

/** RN-PAG-001: a soma das sessões não pode passar do total aprovado. Avisa, não
 * impede — quem recusa é o servidor, e ele não recusa este caso hoje. */
const planNote = computed(() => {
  const { plannedTotal, differsFromTotal, exceedsTotal } = report.value;
  if (plannedTotal === null || !differsFromTotal) {
    return null;
  }
  const planned = money.amount(plannedTotal);
  return exceedsTotal
    ? `The sessions add up to ${planned}, more than the total value.`
    : `The sessions add up to ${planned}, less than the total value.`;
});

function submit(): void {
  emit("submit", {
    clientId: clientId.value,
    artistId: artistId.value === "" ? null : artistId.value,
    fields: {
      origin: selectedOrigin.value,
      description: description.value.trim(),
      bodyRegion: bodyRegion.value.trim(),
      sizeEstimate: sizeEstimate.value.trim(),
      totalValue: totalValue.value.trim(),
      plannedSessions: Number(plannedSessions.value),
      plannedValuePerSession: plannedValuePerSession.value.trim(),
      estimatedDurationMinutes: Number(estimatedDurationMinutes.value),
      notes: notes.value.trim() === "" ? null : notes.value.trim(),
    },
  });
}
</script>

<template>
  <AppModal
    :title="isEditing ? 'Edit quote' : 'New quote'"
    @close="$emit('close')"
  >
    <p
      v-if="decisionWarning"
      class="warning"
      role="alert"
    >
      {{ decisionWarning }}
    </p>

    <AppSelect
      v-if="!isEditing"
      v-model="clientId"
      label="Client"
      placeholder="Choose a client"
      :options="clientOptions"
      :error="report.errors.clientId ?? null"
      :disabled="props.busy"
      required
    />

    <AppSelect
      v-if="!isEditing && props.canChooseArtist && artistOptions.length > 0"
      v-model="artistId"
      label="Artist"
      placeholder="Myself"
      :options="artistOptions"
      :disabled="props.busy"
    />

    <AppSelect
      v-model="origin"
      label="Origin"
      :options="originOptions"
      :disabled="props.busy"
      required
    />

    <p class="share">
      {{ shareNote }}
    </p>

    <AppTextarea
      v-model="description"
      label="Tattoo description"
      :error="report.errors.description ?? null"
      :disabled="props.busy"
      required
    />

    <div class="pair">
      <AppInput
        v-model="bodyRegion"
        label="Body region"
        :error="report.errors.bodyRegion ?? null"
        :disabled="props.busy"
        required
      />
      <AppInput
        v-model="sizeEstimate"
        label="Estimated size"
        :error="report.errors.sizeEstimate ?? null"
        :disabled="props.busy"
        required
      />
    </div>

    <div class="pair">
      <AppInput
        v-model="totalValue"
        label="Total value (€)"
        type="number"
        :error="report.errors.totalValue ?? null"
        :disabled="props.busy"
        required
      />
      <AppInput
        v-model="plannedValuePerSession"
        label="Value per session (€)"
        type="number"
        :error="report.errors.plannedValuePerSession ?? null"
        :disabled="props.busy"
        required
      />
    </div>

    <div class="pair">
      <AppInput
        v-model="plannedSessions"
        label="Planned sessions"
        type="number"
        :error="report.errors.plannedSessions ?? null"
        :disabled="props.busy"
        required
      />
      <AppInput
        v-model="estimatedDurationMinutes"
        label="Minutes per session"
        type="number"
        :error="report.errors.estimatedDurationMinutes ?? null"
        :disabled="props.busy"
        required
      />
    </div>

    <p
      v-if="planNote"
      class="plan"
    >
      {{ planNote }}
    </p>

    <AppTextarea
      v-model="notes"
      label="Notes (optional)"
      :rows="3"
      :error="report.errors.notes ?? null"
      :disabled="props.busy"
    />

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
        :disabled="!report.submittable"
        @click="submit"
      >
        {{ isEditing ? "Save changes" : "Create quote" }}
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
/* O aviso de consequência fica em destaque suave, e não como erro: ele precede
   a decisão, não relata uma falha. Mesmo tratamento do modal de agendamento. */
.warning {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-warning-soft);
  color: var(--color-warning);
  font-size: var(--text-label-3);
}

.share,
.plan {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}

/* Dois campos lado a lado num telefone deixam cada um estreito demais para o
   rótulo caber sem quebrar. */
@media (max-width: 40rem) {
  .pair {
    grid-template-columns: 1fr;
  }
}
</style>
