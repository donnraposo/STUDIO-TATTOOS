<script setup lang="ts">
import { computed, ref } from "vue";

import { QuoteDisplay } from "@/features/quotes/QuoteDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Quote } from "@/shared/domain/Quote";
import { StudioSplit } from "@/shared/domain/StudioSplit";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** O trabalho orçado deste horário, dentro da decisão sobre ele (RN-ORC-002).
 *
 * **Mora aqui porque os dois nascem juntos.** Desde 07/10/2026 o tatuador
 * preenche os dados da tatuagem ao escolher a maca, e a tela própria de
 * orçamentos deixou de existir. O gestor que abre o horário precisa poder
 * aprovar ou recusar o trabalho sem procurá-lo noutro lugar.
 *
 * **São duas decisões, e continuam separadas.** Aprovar o orçamento é a
 * RN-ORC-002; aprovar o horário é a RN-AGE-005 e depende do sinal confirmado.
 * Juntá-las num botão só mudaria regra de negócio — e deixaria o gestor
 * aprovando valor sem reparar que aprovou.
 *
 * **A recusa exige motivo** (RN-ORC-003), e o botão fica travado sem ele: um
 * orçamento recusado sem explicação não diz ao artista o que corrigir.
 *
 * **Mostra o orçamento inteiro**, e não um resumo: é aqui que o gestor confere
 * o que o artista preencheu, e um resumo o obrigaria a procurar o resto noutro
 * lugar que não existe mais. Enquanto o percentual não é congelado, a divisão
 * aparece marcada como ainda não congelada — o número que vale é o que a
 * aprovação gravar (RN-REP-006).
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  quote: Quote;
  canDecide: boolean;
  busy: boolean;
}>();

const emit = defineEmits<{
  approve: [percentage: string | null];
  reject: [reason: string, note: string | null];
}>();

const REASONS: SelectOption[] = [
  { value: "PRICE", label: "Price" },
  { value: "SCOPE", label: "Scope of the work" },
  { value: "OTHER", label: "Other" },
];

const display = new QuoteDisplay();
const money = new MoneyFormatter();
const split = new StudioSplit();

const rejecting = ref(false);
const reason = ref("PRICE");
const note = ref("");
const correction = ref("");

const pending = computed(() => props.quote.status === "PENDING");

/** Vazio usa o padrão: o acordo do artista quando existe, senão a regra da
 * origem. Preenchido corrige **este** atendimento (RN-CLI-003).
 *
 * A conta dos dois lados vem do `StudioSplit`, que é quem a tem. */
const studioKeeps = computed(() =>
  correction.value.trim() === "" ? null : split.studioShareOf(correction.value),
);

function approve(): void {
  emit("approve", correction.value.trim() === "" ? null : correction.value.trim());
}

function reject(): void {
  if (note.value.trim() !== "" || reason.value !== "") {
    emit("reject", reason.value, note.value.trim() === "" ? null : note.value.trim());
  }
}
</script>

<template>
  <section class="work">
    <header>
      <h3>The tattoo</h3>
      <StatusBadge
        :label="display.status(props.quote.status).label"
        :tone="display.status(props.quote.status).tone"
      />
    </header>

    <p class="what">
      {{ props.quote.description }}
    </p>

    <dl class="facts">
      <div>
        <dt>Origin</dt>
        <dd>{{ display.origin(props.quote.origin) }}</dd>
      </div>
      <div>
        <dt>Body region</dt>
        <dd>{{ props.quote.bodyRegion }}</dd>
      </div>
      <div>
        <dt>Size</dt>
        <dd>{{ props.quote.sizeEstimate }}</dd>
      </div>
      <div>
        <dt>Total value</dt>
        <dd>{{ money.amount(props.quote.totalValue) }}</dd>
      </div>
      <div>
        <dt>Per session</dt>
        <dd>{{ money.amount(props.quote.plannedValuePerSession) }}</dd>
      </div>
      <div>
        <dt>Planned sessions</dt>
        <dd>{{ props.quote.plannedSessions }}</dd>
      </div>
      <div>
        <dt>Minutes per session</dt>
        <dd>{{ props.quote.estimatedDurationMinutes }}</dd>
      </div>
      <div>
        <dt>Split</dt>
        <dd>
          <template v-if="props.quote.artistPercentage">
            artist {{ money.percentage(props.quote.artistPercentage) }} ·
            studio {{ split.studioShareOf(props.quote.artistPercentage) }}
          </template>
          <template v-else>
            artist {{ display.standardPercentage(props.quote.origin) }}% ·
            studio {{ split.studioShareForOrigin(props.quote.origin) }}
            <small>(not frozen yet)</small>
          </template>
        </dd>
      </div>
      <div v-if="props.quote.notes">
        <dt>Notes</dt>
        <dd>{{ props.quote.notes }}</dd>
      </div>
      <div v-if="props.quote.rejectionReason">
        <dt>Rejected because</dt>
        <dd>{{ props.quote.rejectionReason }}{{ props.quote.rejectionNote ? ` — ${props.quote.rejectionNote}` : "" }}</dd>
      </div>
    </dl>

    <template v-if="props.canDecide && pending">
      <template v-if="rejecting">
        <AppSelect
          v-model="reason"
          label="Reason"
          :options="REASONS"
          required
          :disabled="props.busy"
        />
        <AppInput
          v-model="note"
          label="Note (optional)"
          :disabled="props.busy"
        />
      </template>

      <template v-else>
        <AppInput
          v-model="correction"
          label="Artist keeps (optional)"
          type="number"
          placeholder="Leave empty to use the standard"
          :disabled="props.busy"
        />
        <p
          v-if="studioKeeps"
          class="hint"
        >
          The studio keeps {{ studioKeeps }} of this session.
        </p>
      </template>

      <div class="actions">
        <AppButton
          tone="ghost"
          :disabled="props.busy"
          @click="rejecting = !rejecting"
        >
          {{ rejecting ? "Back" : "Reject the work" }}
        </AppButton>
        <AppButton
          v-if="rejecting"
          tone="danger"
          :busy="props.busy"
          @click="reject"
        >
          Reject
        </AppButton>
        <AppButton
          v-else
          :busy="props.busy"
          @click="approve"
        >
          Approve the work
        </AppButton>
      </div>
    </template>
  </section>
</template>

<style scoped>
.work {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

h3 {
  margin: var(--space-0);
  font-size: var(--text-label-1);
}

.what {
  margin: var(--space-0);
}

/* Duas colunas: sao nove fatos, e empilhados viram uma lista que ninguem le
   inteira dentro de um modal. */
.facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  margin: var(--space-0);
}

@media (max-width: 40rem) {
  .facts {
    grid-template-columns: 1fr;
  }
}

dd small {
  color: var(--color-muted);
}

dt {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

dd {
  margin: var(--space-0);
}

.hint {
  margin: var(--space-0);
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>
