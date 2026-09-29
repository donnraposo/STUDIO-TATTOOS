<script setup lang="ts">
import { computed, ref } from "vue";

import AppButton from "@/shared/components/AppButton.vue";
import AppCheckbox from "@/shared/components/AppCheckbox.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import type { Booth } from "@/shared/domain/Booking";
import type { Client } from "@/shared/domain/Client";
import type { StudioMember } from "@/shared/domain/StudioMember";

/** Nova reserva de maca (RN-AGE-002).
 *
 * **Quem pode escolher o artista é o gestor.** O residente agenda para si, e
 * por isso o seletor de artista só aparece para quem decide — pedir ao artista
 * que escolha a si mesmo numa lista seria ruído, e escolher outro seria recusado
 * pelo backend de qualquer forma.
 *
 * **Criar já aprovado também é do gestor** (RN-AGE-005). Fica como caixa e não
 * como botão separado, porque é uma variação do mesmo ato, não outro ato.
 *
 * O formulário **não verifica conflito de horário**. Quem decide isso é a
 * restrição do banco, no momento da gravação (ADR-011): conferir aqui e gravar
 * depois reabriria exatamente a janela de corrida que a restrição fecha, e
 * daria uma resposta que pode estar desatualizada no instante seguinte. */
export interface BookingDraft {
  clientId: string;
  boothId: string;
  startTime: string;
  endTime: string;
  artistId: string | null;
  approveImmediately: boolean;
}

const props = defineProps<{
  day: string;
  clients: Client[];
  booths: Booth[];
  artists: StudioMember[];
  canDecide: boolean;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ submit: [draft: BookingDraft]; close: [] }>();

const clientId = ref("");
const boothId = ref(props.booths[0]?.id ?? "");
const artistId = ref("");
const startTime = ref("10:00");
const endTime = ref("12:00");
const approveImmediately = ref(false);

const clientOptions = computed<SelectOption[]>(() =>
  props.clients.map((client) => ({ value: client.id, label: client.name })),
);

const boothOptions = computed<SelectOption[]>(() =>
  props.booths.map((booth) => ({ value: booth.id, label: `Booth ${booth.number}` })),
);

const artistOptions = computed<SelectOption[]>(() =>
  props.artists.map((artist) => ({ value: artist.id, label: artist.displayName })),
);

/** O fim precisa ser depois do início. É a única regra conferida aqui, porque
 * não depende do estado do estúdio — ninguém precisa consultar o banco para
 * saber que um intervalo vazio não é um agendamento. */
const invalidPeriod = computed(() => endTime.value <= startTime.value);

const incomplete = computed(
  () => clientId.value === "" || boothId.value === "" || invalidPeriod.value,
);

function submit(): void {
  emit("submit", {
    clientId: clientId.value,
    boothId: boothId.value,
    startTime: startTime.value,
    endTime: endTime.value,
    artistId: artistId.value === "" ? null : artistId.value,
    approveImmediately: approveImmediately.value,
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
      v-model="boothId"
      label="Booth"
      :options="boothOptions"
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

    <AppCheckbox
      v-if="props.canDecide"
      v-model="approveImmediately"
      label="Approve straight away"
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
        :disabled="incomplete"
        @click="submit"
      >
        {{ props.canDecide && approveImmediately ? "Create and approve" : "Request booking" }}
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

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
