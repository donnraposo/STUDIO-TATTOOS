<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import QuoteDetail from "@/features/quotes/components/QuoteDetail.vue";
import SessionDecisionModal from "@/features/quotes/components/SessionDecisionModal.vue";
import QuoteForm, { type QuoteDraft } from "@/features/quotes/components/QuoteForm.vue";
import QuoteList from "@/features/quotes/components/QuoteList.vue";
import { ApiError } from "@/shared/api/ApiError";
import { useApi } from "@/shared/api/useApi";
import { useAsyncState } from "@/shared/async/useAsyncState";
import AppButton from "@/shared/components/AppButton.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import ErrorState from "@/shared/components/ErrorState.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import type { Client } from "@/shared/domain/Client";
import type { Quote, ReferenceImage } from "@/shared/domain/Quote";
import type { TattooSession } from "@/shared/domain/TattooSession";
import type { StudioMember } from "@/shared/domain/StudioMember";
import { StudioClock } from "@/shared/format/StudioClock";
import { useSession } from "@/shared/session/useSession";

/** Orçamentos (RN-ORC-001 a RN-ORC-004 e RN-REP-006).
 *
 * A única peça desta pasta que fala com a API; os componentes ao lado recebem
 * tudo por `props`.
 *
 * **O recorte do que se vê é do backend.** O gestor recebe todos os orçamentos,
 * o residente recebe os seus. A tela não filtra: filtrar aqui daria duas
 * versões da RN-ORC-001, e a do navegador é a que ficaria para trás sem
 * ninguém notar. O que a tela faz é **explicar** o recorte, para que o artista
 * não conclua que o estúdio tem dois orçamentos no total.
 *
 * **O guest não chega aqui pelo menu** (RN-ORC-001), e quem digitar o endereço
 * recebe 403 na listagem — que o `AsyncState` mostra sem oferecer "tentar de
 * novo", porque insistir não muda permissão. */
interface QuotesBoard {
  quotes: Quote[];
  clients: Client[];
  artists: StudioMember[];
}

const { quotes: quotesApi, sessions: sessionsApi, clients: clientsApi, accounts } = useApi();
const { session, permissions } = useSession();
const clock = new StudioClock();

const state = useAsyncState<QuotesBoard>();
const selected = ref<Quote | null>(null);
const composing = ref(false);
const editing = ref<Quote | null>(null);
const busy = ref(false);
const failure = ref<string | null>(null);
const images = ref<ReferenceImage[]>([]);
const sessions = ref<TattooSession[]>([]);
const deciding = ref<{ session: TattooSession; mode: "mark" | "confirm" } | null>(null);
const imagesBusy = ref(false);
const imagesFailure = ref<string | null>(null);

const user = session.user;

const isStaff = computed(() => (user.value ? permissions.isStaff(user.value) : false));
const canDecide = computed(() => (user.value ? permissions.canDecide(user.value) : false));
const canCreate = computed(() => (user.value ? permissions.canSeeQuotes(user.value) : false));

const scopeNote = computed(() =>
  isStaff.value
    ? "Every quote in the studio."
    : "Only your own quotes. The studio management sees all of them.",
);

const heading = computed(() => {
  const total = state.data.value?.quotes.length ?? 0;
  return `${total} quote${total === 1 ? "" : "s"}`;
});

/** RN-ORC-003: o gestor edita sempre; o artista edita o próprio orçamento
 * **enquanto pendente**. É a mesma decisão do `QuotePolicy`, e continua sendo
 * aparência — o backend recusa com 403 de qualquer forma. */
/** RN-ORC-005: o artista marca a própria sessão como realizada; o gestor
 * também, porque opera o sistema por quem não registrou e responde pelo guest,
 * que não acessa o módulo (RN-ORC-001). */
const canMarkSelected = computed(() => {
  const quote = selected.value;
  const current = user.value;
  return Boolean(quote && current && (isStaff.value || current.id === quote.artistId));
});

const canEditSelected = computed(() => {
  const quote = selected.value;
  const current = user.value;
  if (!quote || !current) {
    return false;
  }
  return isStaff.value || (current.id === quote.artistId && quote.status === "PENDING");
});

const namesByClient = computed<Record<string, string>>(() =>
  Object.fromEntries((state.data.value?.clients ?? []).map((client) => [client.id, client.name])),
);

/** O próprio usuário entra no mapa de artistas.
 *
 * O residente não lista contas — recebe 403 — e todos os orçamentos que ele vê
 * são dele. Sem esta linha, o cartão de cada um deles mostraria "Artist" no
 * lugar do nome de quem está olhando a tela. */
const namesByArtist = computed<Record<string, string>>(() => {
  const named = Object.fromEntries(
    (state.data.value?.artists ?? []).map((artist) => [artist.id, artist.displayName]),
  );
  const current = user.value;
  if (current && !(current.id in named)) {
    named[current.id] = current.fullName;
  }
  return named;
});

async function load(): Promise<void> {
  await state.run(async () => ({
    quotes: await quotesApi.list(),
    clients: await visibleClients(),
    artists: await knownArtists(),
  }));
}

/** Falhar em buscar clientes não derruba a lista de orçamentos: sem nome é
 * menos informação, sem lista é tela quebrada. */
async function visibleClients(): Promise<Client[]> {
  try {
    return await clientsApi.list();
  } catch {
    return [];
  }
}

/** Só o gestor lista contas. O residente orça para si, e o seletor de artista
 * nem aparece para ele. */
async function knownArtists(): Promise<StudioMember[]> {
  try {
    return await accounts.listArtists();
  } catch {
    return [];
  }
}

/** Toda ação passa por aqui: ocupa, limpa o erro anterior, tenta, recarrega e
 * reencontra o orçamento aberto na lista nova.
 *
 * O reencontro importa mais do que parece. Editar um aprovado o devolve a
 * pendente (RN-ORC-003); se o modal continuasse mostrando a cópia antiga, ele
 * exibiria "Approved" e um percentual que acabou de ser descartado. */
async function act(action: () => Promise<unknown>, keepOpen: boolean): Promise<void> {
  busy.value = true;
  failure.value = null;
  try {
    await action();
    composing.value = false;
    editing.value = null;
    await load();
    selected.value = keepOpen ? refreshed(selected.value) : null;
    deciding.value = null;
    if (selected.value) {
      await loadSessions(selected.value.id);
    }
  } catch (error) {
    failure.value =
      error instanceof ApiError ? error.message : "Could not reach the studio system.";
  } finally {
    busy.value = false;
  }
}

function refreshed(quote: Quote | null): Quote | null {
  return quote
    ? (state.data.value?.quotes.find((candidate) => candidate.id === quote.id) ?? null)
    : null;
}

async function open(quote: Quote): Promise<void> {
  selected.value = quote;
  failure.value = null;
  await Promise.all([loadImages(quote.id), loadSessions(quote.id)]);
}

/** As sessões do orçamento aberto (RN-ORC-005).
 *
 * Falhar aqui não derruba o detalhe: um orçamento pendente não tem sessões, e
 * quem não pode vê-las recebe 403 — nos dois casos a lista vazia é resposta
 * melhor do que uma tela que não abre. */
async function loadSessions(quoteId: string): Promise<void> {
  try {
    sessions.value = await sessionsApi.listForQuote(quoteId);
  } catch {
    sessions.value = [];
  }
}

/** Marcar e confirmar recarregam **as sessões e o orçamento**.
 *
 * O orçamento porque a RN-ORC-006 pode devolvê-lo a Pendente quando um ajuste
 * muda o valor comprometido; sem recarregar, o modal continuaria mostrando
 * "Approved" sobre um orçamento que deixou de estar. */
async function markPerformed(chargedValue: string | null): Promise<void> {
  const target = deciding.value;
  if (target) {
    await act(() => sessionsApi.markPerformed(target.session.id, chargedValue), true);
  }
}

async function confirmReceipt(
  chargedValue: string | null,
  reason: string | null,
): Promise<void> {
  const target = deciding.value;
  if (target) {
    await act(
      () => sessionsApi.confirmPayment(target.session.id, chargedValue, reason),
      true,
    );
  }
}

async function loadImages(quoteId: string): Promise<void> {
  imagesBusy.value = true;
  imagesFailure.value = null;
  images.value = [];
  try {
    images.value = await quotesApi.listImages(quoteId);
  } catch (error) {
    imagesFailure.value =
      error instanceof ApiError ? error.message : "Could not load the reference images.";
  } finally {
    imagesBusy.value = false;
  }
}

function startCreating(): void {
  editing.value = null;
  failure.value = null;
  composing.value = true;
}

function startEditing(): void {
  editing.value = selected.value;
  failure.value = null;
  composing.value = true;
}

async function save(draft: QuoteDraft): Promise<void> {
  const target = editing.value;
  await act(
    () =>
      target
        ? quotesApi.update(target.id, draft.fields)
        : quotesApi.create(draft.clientId, draft.fields, draft.artistId),
    target !== null,
  );
}

async function approve(artistPercentage: string | null): Promise<void> {
  const quote = selected.value;
  if (quote) {
    await act(() => quotesApi.approve(quote.id, artistPercentage), true);
  }
}

async function reject(reason: string, note: string | null): Promise<void> {
  const quote = selected.value;
  if (quote) {
    await act(() => quotesApi.reject(quote.id, reason, note), true);
  }
}

/** Anexar e remover imagem não mexem no orçamento, então não recarregam a lista
 * inteira: só a lista de imagens do orçamento aberto. */
async function attach(file: File): Promise<void> {
  const quote = selected.value;
  if (!quote) {
    return;
  }
  imagesBusy.value = true;
  imagesFailure.value = null;
  try {
    await quotesApi.attachImage(quote.id, file);
  } catch (error) {
    imagesFailure.value =
      error instanceof ApiError ? error.message : "Could not attach the image.";
  } finally {
    imagesBusy.value = false;
  }
  await loadImages(quote.id);
}

async function remove(imageId: string): Promise<void> {
  const quote = selected.value;
  if (!quote) {
    return;
  }
  imagesBusy.value = true;
  imagesFailure.value = null;
  try {
    await quotesApi.removeImage(quote.id, imageId);
  } catch (error) {
    imagesFailure.value =
      error instanceof ApiError ? error.message : "Could not remove the image.";
  } finally {
    imagesBusy.value = false;
  }
  await loadImages(quote.id);
}

onMounted(load);
</script>

<template>
  <div class="quotes">
    <PageHeader
      kicker="Studio workspace"
      :title="heading"
    >
      <template #actions>
        <AppButton
          v-if="canCreate"
          :disabled="state.isLoading.value"
          @click="startCreating"
        >
          New quote
        </AppButton>
      </template>
    </PageHeader>

    <p class="scope">
      {{ scopeNote }}
    </p>

    <LoadingState v-if="state.isLoading.value" />

    <ErrorState
      v-else-if="state.error.value"
      :message="state.errorMessage.value"
      :retryable="state.isRetryable.value"
      @retry="state.retry()"
    />

    <EmptyState
      v-else-if="state.data.value && state.data.value.quotes.length === 0"
      title="No quotes yet"
      description="Create the first quote to plan a tattoo and its sessions."
    >
      <template #action>
        <AppButton
          v-if="canCreate"
          @click="startCreating"
        >
          New quote
        </AppButton>
      </template>
    </EmptyState>

    <QuoteList
      v-else-if="state.data.value"
      :quotes="state.data.value.quotes"
      :client-names="namesByClient"
      :artist-names="namesByArtist"
      @open="open"
    />

    <QuoteForm
      v-if="composing && state.data.value"
      :quote="editing"
      :self-artist-id="user?.id ?? null"
      :clients="state.data.value.clients"
      :artists="state.data.value.artists"
      :can-choose-artist="isStaff"
      :busy="busy"
      :failure="failure"
      @submit="save"
      @close="composing = false"
    />

    <QuoteDetail
      v-else-if="selected"
      :quote="selected"
      :client-name="namesByClient[selected.clientId] ?? 'Client'"
      :artist-name="namesByArtist[selected.artistId] ?? 'Artist'"
      :created-at="clock.dateTime(selected.createdAt)"
      :decided-at="selected.approvedAt ? clock.dateTime(selected.approvedAt) : null"
      :images="images"
      :can-decide="canDecide"
      :can-edit="canEditSelected"
      :sessions="sessions"
      :can-mark-sessions="canMarkSelected"
      :busy="busy"
      :failure="failure"
      :images-busy="imagesBusy"
      :images-failure="imagesFailure"
      @edit="startEditing"
      @approve="approve"
      @reject="reject"
      @attach="attach"
      @remove="remove"
      @close="selected = null"
      @mark-session="deciding = { session: $event, mode: 'mark' }"
      @confirm-session="deciding = { session: $event, mode: 'confirm' }"
    />

    <SessionDecisionModal
      v-if="deciding"
      :session="deciding.session"
      :mode="deciding.mode"
      :busy="busy"
      :failure="failure"
      @mark="markPerformed"
      @confirm="confirmReceipt"
      @close="deciding = null"
    />
  </div>
</template>

<style scoped>
.quotes {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.scope {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
