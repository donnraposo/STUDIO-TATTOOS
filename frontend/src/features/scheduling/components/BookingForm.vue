<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { DepositRequirement } from "@/features/scheduling/DepositRequirement";
import AppButton from "@/shared/components/AppButton.vue";
import AppCheckbox from "@/shared/components/AppCheckbox.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import { BookingDeposit } from "@/features/payments/BookingDeposit";
import AppTextarea from "@/shared/components/AppTextarea.vue";
import type { Bench } from "@/shared/domain/Booking";
import type { Client } from "@/shared/domain/Client";
import type { QuoteOrigin } from "@/shared/domain/Quote";
import { SessionValues } from "@/shared/domain/SessionValues";
import { StudioSplit } from "@/shared/domain/StudioSplit";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";
import type { StudioMember } from "@/shared/domain/StudioMember";

/** Nova reserva de maca (RN-AGE-002).
 *
 * **Quem pode escolher o artista é o gestor.** O residente agenda para si, e
 * por isso o seletor de artista só aparece para quem decide — pedir ao artista
 * que escolha a si mesmo numa lista seria ruído, e escolher outro seria recusado
 * pelo backend de qualquer forma.
 *
 * **Criar já aprovado vale onde não há sinal a confirmar.** A RN-AGE-005 permite
 * o atalho *"desde que confirmem o sinal"*, e o sinal pertence ao agendamento —
 * que ainda não existe no instante da criação (ADR-027). O caminho corrente é
 * criar, confirmar o sinal e aprovar; a caixa só aparece onde a regra não pede
 * sinal, que é o cliente próprio do guest (RN-GST-004).
 *
 * A tela **esconde** o atalho em vez de oferecê-lo e levar 403: um botão que o
 * servidor recusa ensina a equipe a desconfiar dos próprios botões. Quem garante
 * continua sendo o backend.
 *
 * O formulário **não verifica conflito de horário**. Quem decide isso é a
 * restrição do banco, no momento da gravação (ADR-011): conferir aqui e gravar
 * depois reabriria exatamente a janela de corrida que a restrição fecha, e
 * daria uma resposta que pode estar desatualizada no instante seguinte.
 *
 * **Os dados da tatuagem são preenchidos aqui, ao escolher a maca** (decisão de
 * 07/10/2026). Antes disso o orçamento tinha tela própria, e o artista marcava
 * o horário num lugar e descrevia o trabalho noutro — duas visitas para um ato
 * só, e nada ligando as duas.
 *
 * **O guest não vê esta parte.** A RN-ORC-001 tira dele o módulo de orçamentos
 * e o mantém na agenda para clientes próprios. Oferecer-lhe os campos seria
 * oferecer uma tela que o servidor recusa.
 *
 * **A duração não é campo.** Ela sai do início e do fim que já estão acima;
 * perguntá-la de novo abriria a chance de os dois números discordarem, e o
 * horário na grade é o que o estúdio enxerga.
 *
 * **Cada agendamento é um trabalho**, por decisão do responsável: um orçamento
 * por sessão, com "sessão N de M" na descrição para que se saiba onde aquele
 * atendimento cai dentro do trabalho maior. */
export interface BookingWork {
  origin: QuoteOrigin;
  description: string;
  bodyRegion: string;
  sizeEstimate: string;
  totalValue: string;
  valuePerSession: string;
  plannedSessions: number;
  sessionNumber: number;
  notes: string | null;
}

export interface BookingDraft {
  /** O sinal que o artista diz ter combinado. Vazio usa o padrão do estúdio. */
  depositAmount: string;
  clientId: string;
  benchId: string;
  startTime: string;
  endTime: string;
  artistId: string | null;
  approveImmediately: boolean;
  /** Nulo quando quem agenda não tem orçamento: o guest, pela RN-ORC-001. */
  work: BookingWork | null;
}

const props = defineProps<{
  day: string;
  clients: Client[];
  benches: Bench[];
  artists: StudioMember[];
  canDecide: boolean;
  /** RN-ORC-001: o guest não acessa orçamentos, e para ele os campos somem. */
  canQuote: boolean;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ submit: [draft: BookingDraft]; close: [] }>();

const clientId = ref("");
const benchId = ref(props.benches[0]?.id ?? "");
const artistId = ref("");
const startTime = ref("10:00");
const endTime = ref("12:00");
const approveImmediately = ref(false);
const depositAmount = ref(BookingDeposit.AMOUNT);

const ORIGIN_OPTIONS: SelectOption[] = [
  { value: "ARTIST_OWN", label: "The artist's own client" },
  { value: "STUDIO_REFERRAL", label: "Referred by the studio" },
];

const origin = ref<string>("ARTIST_OWN");
const description = ref("");
const bodyRegion = ref("");
const sizeEstimate = ref("");
const totalValue = ref("");
const valuePerSession = ref("");
const plannedSessions = ref("1");
const sessionNumber = ref("1");
const notes = ref("");

const clientOptions = computed<SelectOption[]>(() =>
  props.clients.map((client) => ({ value: client.id, label: client.name })),
);

const benchOptions = computed<SelectOption[]>(() =>
  props.benches.map((bench) => ({ value: bench.id, label: `Bench ${bench.number}` })),
);

const artistOptions = computed<SelectOption[]>(() =>
  props.artists.map((artist) => ({ value: artist.id, label: artist.displayName })),
);

/** O fim precisa ser depois do início. É a única regra conferida aqui, porque
 * não depende do estado do estúdio — ninguém precisa consultar o banco para
 * saber que um intervalo vazio não é um agendamento. */
const invalidPeriod = computed(() => endTime.value <= startTime.value);

const deposits = new DepositRequirement();

/** O atalho de criar já aprovado só existe onde não há sinal a confirmar. */
const needsDeposit = computed(() => deposits.appliesTo(artistId.value, props.artists));

/** O que o estúdio fica nesta origem, dito do lado dele — que é como os
 * acordos são enunciados. A conta mora no `StudioSplit`: escrevê-la aqui seria
 * a terceira cópia da mesma regra. */
const split = new StudioSplit();
const money = new MoneyFormatter();

const studioShare = computed(() => split.studioShareForOrigin(origin.value as QuoteOrigin));
const artistShare = computed(() => `${split.artistShareFor(origin.value as QuoteOrigin)}%`);

const values = new SessionValues();

/** Preencher um preenche o outro. Pedir os dois seria pedir ao tatuador a conta
 * que o sistema faz — e abrir a chance de os dois números discordarem, que é
 * pior do que faltar um: o repasse sairia de um e o orçamento aprovado do
 * outro. */
/** Qual dos dois o tatuador escreveu por último. O outro é derivado dele, e
 * nunca o contrário.
 *
 * **Sem isto, o sistema reescrevia o que a pessoa acabou de digitar.** Os
 * observadores do Vue correm depois do evento: digitar três sessões e então mil
 * de total fazia o observador rodar por último e devolver €999,99 ao campo —
 * derivando o total de um valor por sessão que ele mesmo tinha arredondado.
 * Quem digitou mil via novecentos e noventa e nove. */
const driving = ref<"total" | "session">("total");

function fillFromTotal(): void {
  driving.value = "total";
  valuePerSession.value = values.perSessionFrom(
    totalValue.value,
    Number(plannedSessions.value) || 1,
  );
}

function fillFromSession(): void {
  driving.value = "session";
  totalValue.value = values.totalFrom(valuePerSession.value, Number(plannedSessions.value) || 1);
}

/** Mudar o número de sessões recalcula **o campo derivado**, nunca o que foi
 * digitado: quem disse "são quatro em vez de três" não espera ver o próprio
 * número trocar. */
watch(plannedSessions, () => {
  const sessions = Number(plannedSessions.value) || 1;
  if (driving.value === "session") {
    totalValue.value = values.totalFrom(valuePerSession.value, sessions);
  } else {
    valuePerSession.value = values.perSessionFrom(totalValue.value, sessions);
  }
});

const workIncomplete = computed(
  () =>
    props.canQuote &&
    (description.value.trim() === "" ||
      bodyRegion.value.trim() === "" ||
      sizeEstimate.value.trim() === "" ||
      !values.isComplete(totalValue.value, valuePerSession.value) ||
      Number(plannedSessions.value) < 1),
);

const incomplete = computed(
  () =>
    clientId.value === "" ||
    benchId.value === "" ||
    invalidPeriod.value ||
    workIncomplete.value,
);

function submit(): void {
  emit("submit", {
    clientId: clientId.value,
    benchId: benchId.value,
    startTime: startTime.value,
    endTime: endTime.value,
    artistId: artistId.value === "" ? null : artistId.value,
    approveImmediately: approveImmediately.value,
    depositAmount: depositAmount.value.trim(),
    work: props.canQuote
      ? {
          origin: origin.value as QuoteOrigin,
          description: description.value.trim(),
          bodyRegion: bodyRegion.value.trim(),
          sizeEstimate: sizeEstimate.value.trim(),
          totalValue: totalValue.value.trim(),
          valuePerSession: valuePerSession.value.trim(),
          plannedSessions: Number(plannedSessions.value) || 1,
          sessionNumber: Number(sessionNumber.value) || 1,
          notes: notes.value.trim() === "" ? null : notes.value.trim(),
        }
      : null,
  });
}
</script>

<template>
  <AppModal
    title="New booking"
    @close="$emit('close')"
  >
    <p class="day">
      {{ props.day }}
    </p>

    <AppSelect
      v-model="clientId"
      label="Client"
      placeholder="Choose a client"
      :options="clientOptions"
      :disabled="props.busy"
      required
    />

    <AppSelect
      v-model="benchId"
      label="Bench"
      :options="benchOptions"
      :disabled="props.busy"
      required
    />

    <AppSelect
      v-if="props.canDecide && artistOptions.length > 0"
      v-model="artistId"
      label="Artist"
      placeholder="Myself"
      :options="artistOptions"
      :disabled="props.busy"
    />

    <div class="period">
      <AppInput
        v-model="startTime"
        label="Start"
        type="time"
        :disabled="props.busy"
        required
      />
      <AppInput
        v-model="endTime"
        label="End"
        type="time"
        :error="invalidPeriod ? 'The end must be after the start.' : null"
        :disabled="props.busy"
        required
      />
    </div>

    <section
      v-if="props.canQuote"
      class="work"
    >
      <h4>The tattoo</h4>

      <AppSelect
        v-model="origin"
        label="Where this client came from"
        :options="ORIGIN_OPTIONS"
        required
        :disabled="props.busy"
      />
      <p class="hint">
        Studio default for this origin: the artist keeps
        {{ artistShare }}, the studio keeps {{ studioShare }}.
      </p>

      <AppTextarea
        v-model="description"
        label="What is being tattooed"
        :rows="3"
        required
        :disabled="props.busy"
      />

      <div class="period">
        <AppInput
          v-model="bodyRegion"
          label="Body region"
          required
          :disabled="props.busy"
        />
        <AppInput
          v-model="sizeEstimate"
          label="Size"
          placeholder="20cm"
          required
          :disabled="props.busy"
        />
      </div>

      <AppInput
        v-model="plannedSessions"
        label="Planned sessions"
        type="number"
        required
        :disabled="props.busy"
      />

      <div class="period">
        <AppInput
          v-model="totalValue"
          label="Total value (€)"
          type="number"
          :disabled="props.busy"
          @update:model-value="fillFromTotal"
        />
        <AppInput
          v-model="valuePerSession"
          label="Value per session (€)"
          type="number"
          :disabled="props.busy"
          @update:model-value="fillFromSession"
        />
      </div>
      <p class="hint">
        Fill in whichever you have — the other one follows.
      </p>

      <AppInput
        v-model="sessionNumber"
        label="This booking is session number"
        type="number"
        :disabled="props.busy"
      />
      <p class="hint">
        Goes into the description, so everyone sees where this sitting falls
        inside the work — "Session {{ sessionNumber }} of {{ plannedSessions }}".
      </p>

      <AppInput
        v-model="depositAmount"
        label="Deposit received (€)"
        type="number"
        :disabled="props.busy"
      />
      <p class="hint">
        What this client paid as a deposit. Each artist charges their own — the
        studio default is {{ money.amount(BookingDeposit.AMOUNT) }}. It arrives
        filled in when the studio registers the payment, and can be corrected
        there.
      </p>

      <AppTextarea
        v-model="notes"
        label="Notes (optional)"
        :rows="2"
        :disabled="props.busy"
      />
    </section>

    <AppCheckbox
      v-if="props.canDecide && !needsDeposit"
      v-model="approveImmediately"
      label="Approve straight away"
      :disabled="props.busy"
    />

    <p
      v-else-if="props.canDecide"
      class="deposit"
    >
      The deposit has to be registered and confirmed before this booking can be
      approved. Create the request first, then confirm the deposit.
    </p>

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
        :disabled="incomplete"
        @click="submit"
      >
        {{ approveImmediately ? "Create and approve" : "Request booking" }}
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.day {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.period {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

/* Dois campos de hora lado a lado num telefone deixam cada um com pouco mais
   de cem pixels, e o seletor nativo fica dificil de operar. */
@media (max-width: 40rem) {
  .period {
    grid-template-columns: 1fr;
  }
}

/* A exigência do sinal é informação que precede a decisão, não erro: tom suave,
   como as consequências do modal de agendamento. */
.deposit {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-warning-soft);
  color: var(--color-warning);
  font-size: var(--text-label-3);
}

/* Os dados da tatuagem em bloco proprio, separados por uma linha: maca e
   horario sao uma pergunta, o que sera tatuado e outra. */
.work {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-top: var(--space-4);
  border-top: var(--border-thin);
}

h4 {
  margin: var(--space-0);
  font-size: var(--text-label-1);
}

.hint {
  margin: var(--space-0);
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
