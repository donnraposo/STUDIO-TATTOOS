<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { Client, ClientSource } from "@/shared/domain/Client";
import type { StudioMember } from "@/shared/domain/StudioMember";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";

/** Cadastro e edição de cliente (RN-CLI-001).
 *
 * Nome e telefone obrigatórios, Instagram opcional. O mesmo formulário serve
 * aos dois casos: `client` nulo cria, preenchido edita. Dois componentes quase
 * iguais divergiriam na primeira mudança de campo.
 *
 * O estado dos campos é interno e copiado de `client` — não escreve na entidade
 * recebida. Editar o objeto do pai faria a lista mudar enquanto se digita, e
 * cancelar não teria como desfazer.
 *
 * **De onde o cliente veio é pergunta do cadastro** (RN-CLI-002): ou um artista
 * o trouxe, ou foi indicação do estúdio. A resposta informa a origem de todo
 * atendimento futuro dele, e por isso vale perguntar uma vez, aqui, em vez de
 * adivinhar a cada orçamento.
 *
 * **Na edição ela só aparece para o gestor** (RN-CLI-003): alterar a origem é
 * dele. Para os demais, o campo some e o formulário manda `source` nulo, que o
 * backend entende como "não toque". Sem isso, o artista corrigindo um telefone
 * levaria 403 por causa de um campo que ele nem viu. */
export interface ClientDraft {
  name: string;
  phone: string;
  instagram: string | null;
  source: ClientSource | null;
  broughtByArtistId: string | null;
}

const props = defineProps<{
  client: Client | null;
  artists: StudioMember[];
  canChooseArtist: boolean;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ submit: [values: ClientDraft]; cancel: [] }>();

const SOURCE_OPTIONS: SelectOption[] = [
  { value: "ARTIST", label: "Brought by an artist" },
  { value: "STUDIO", label: "Studio referral" },
];

const name = ref("");
const phone = ref("");
const instagram = ref("");
const source = ref<string>("ARTIST");
const broughtBy = ref("");

/** O gestor corrige a origem; os demais só a definem ao cadastrar. */
const canSetSource = computed(() => props.client === null || props.canChooseArtist);

const artistOptions = computed<SelectOption[]>(() =>
  props.artists.map((artist) => ({ value: artist.id, label: artist.displayName })),
);

watch(
  () => props.client,
  (client) => {
    name.value = client?.name ?? "";
    phone.value = client?.phone ?? "";
    instagram.value = client?.instagram ?? "";
    source.value = client && client.broughtByArtistId === null ? "STUDIO" : "ARTIST";
    broughtBy.value = client?.broughtByArtistId ?? "";
  },
  { immediate: true },
);

function submit(): void {
  emit("submit", {
    name: name.value,
    phone: phone.value,
    instagram: instagram.value.trim() === "" ? null : instagram.value,
    source: canSetSource.value ? (source.value as ClientSource) : null,
    broughtByArtistId:
      canSetSource.value && source.value === "ARTIST" && broughtBy.value !== ""
        ? broughtBy.value
        : null,
  });
}
</script>

<template>
  <AppCard :title="props.client ? 'Edit client' : 'New client'">
    <form
      class="form"
      @submit.prevent="submit"
    >
      <AppInput
        v-model="name"
        label="Name"
        required
        :disabled="props.busy"
      />
      <AppInput
        v-model="phone"
        label="Phone"
        type="tel"
        required
        :disabled="props.busy"
      />
      <AppInput
        v-model="instagram"
        label="Instagram"
        placeholder="@handle"
        :disabled="props.busy"
      />

      <template v-if="canSetSource">
        <AppSelect
          v-model="source"
          label="Where this client came from"
          :options="SOURCE_OPTIONS"
          :disabled="props.busy"
          required
        />

        <AppSelect
          v-if="props.canChooseArtist && source === 'ARTIST' && artistOptions.length > 0"
          v-model="broughtBy"
          label="Artist who brought them"
          placeholder="Myself"
          :options="artistOptions"
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

      <div class="actions">
        <AppButton
          tone="ghost"
          :disabled="props.busy"
          @click="$emit('cancel')"
        >
          Cancel
        </AppButton>
        <AppButton
          type="submit"
          :busy="props.busy"
        >
          {{ props.client ? "Save changes" : "Create client" }}
        </AppButton>
      </div>
    </form>
  </AppCard>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>
