<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { ApiError } from "@/shared/api/ApiError";
import type { Client, ClientContact } from "@/shared/domain/Client";
import type { StudioMember } from "@/shared/domain/StudioMember";
import { useApi } from "@/shared/api/useApi";
import { useAsyncState } from "@/shared/async/useAsyncState";
import AppButton from "@/shared/components/AppButton.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import ErrorState from "@/shared/components/ErrorState.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import { useSession } from "@/shared/session/useSession";
import ClientForm, { type ClientDraft } from "@/features/clients/components/ClientForm.vue";
import ClientList from "@/features/clients/components/ClientList.vue";
import DuplicateWarning from "@/features/clients/components/DuplicateWarning.vue";

/** Tela de clientes.
 *
 * É a única peça desta pasta que fala com a API; os componentes ao lado
 * recebem tudo por `props`.
 *
 * **A visibilidade da RN-CLI-004 não é aplicada aqui.** O backend já devolve
 * apenas o que o ator pode ver: o gestor recebe todos os clientes, o residente
 * recebe os que cadastrou. A tela não filtra nada — se filtrasse, teria de
 * acertar a mesma regra duas vezes, e a versão do frontend seria a que
 * silenciosamente ficaria para trás. O que a tela faz é **explicar** o recorte,
 * para que o residente não conclua que o estúdio tem três clientes no total. */
const { clients: clientsApi, accounts } = useApi();
const { session, permissions } = useSession();

const state = useAsyncState<Client[]>();
const artists = ref<StudioMember[]>([]);
const editing = ref<Client | null>(null);
const composing = ref(false);
const saving = ref(false);
const saveFailure = ref<string | null>(null);
const duplicates = ref<ClientContact[]>([]);

const user = session.user;

const isStaff = computed(() => (user.value ? permissions.isStaff(user.value) : false));

const scopeNote = computed(() =>
  isStaff.value
    ? "Every client registered in the studio."
    : "Only the clients you registered. The studio sees all of them.",
);

async function load(): Promise<void> {
  await state.run(() => clientsApi.list());
}

/** Só o gestor lista contas; os demais recebem 403 e cadastram para si, que é o
 * caso em que o seletor de artista nem aparece. Falhar aqui não derruba a tela:
 * sem a lista, o formulário some um campo, não a página inteira. */
async function loadArtists(): Promise<void> {
  try {
    artists.value = await accounts.listArtists();
  } catch {
    artists.value = [];
  }
}

function startCreating(): void {
  editing.value = null;
  composing.value = true;
  saveFailure.value = null;
}

function startEditing(client: Client): void {
  editing.value = client;
  composing.value = true;
  saveFailure.value = null;
}

function stopComposing(): void {
  composing.value = false;
  editing.value = null;
  saveFailure.value = null;
}

async function save(values: ClientDraft): Promise<void> {
  saving.value = true;
  saveFailure.value = null;
  try {
    if (editing.value) {
      await clientsApi.update(editing.value.id, values);
      duplicates.value = [];
    } else {
      const registered = await clientsApi.register({
        ...values,
        source: values.source ?? "ARTIST",
      });
      duplicates.value = registered.possibleDuplicates;
    }
    stopComposing();
    await load();
  } catch (error) {
    saveFailure.value =
      error instanceof ApiError ? error.message : "Could not reach the studio system.";
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void load();
  void loadArtists();
});
</script>

<template>
  <div class="clients">
    <PageHeader
      kicker="Studio workspace"
      title="Clients"
    >
      <template #actions>
        <AppButton @click="startCreating">
          New client
        </AppButton>
      </template>
    </PageHeader>

    <p class="scope">
      {{ scopeNote }}
    </p>

    <DuplicateWarning
      v-if="duplicates.length > 0"
      :duplicates="duplicates"
      @dismiss="duplicates = []"
    />

    <ClientForm
      v-if="composing"
      :client="editing"
      :artists="artists"
      :can-choose-artist="isStaff"
      :busy="saving"
      :failure="saveFailure"
      @submit="save"
      @cancel="stopComposing"
    />

    <LoadingState v-if="state.isLoading.value" />

    <ErrorState
      v-else-if="state.error.value"
      :message="state.errorMessage.value"
      :retryable="state.isRetryable.value"
      @retry="state.retry()"
    />

    <EmptyState
      v-else-if="state.isEmpty.value"
      title="No clients yet"
      description="Register the first client to start booking sessions."
    >
      <template #action>
        <AppButton @click="startCreating">
          New client
        </AppButton>
      </template>
    </EmptyState>

    <ClientList
      v-else-if="state.data.value"
      :clients="state.data.value"
      :can-edit="true"
      @edit="startEditing"
    />
  </div>
</template>

<style scoped>
.clients {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.scope {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
