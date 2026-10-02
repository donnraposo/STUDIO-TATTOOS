<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import PayoutList from "@/features/payouts/components/PayoutList.vue";
import PayoutStatementModal from "@/features/payouts/components/PayoutStatementModal.vue";
import { ApiError } from "@/shared/api/ApiError";
import { useApi } from "@/shared/api/useApi";
import { useAsyncState } from "@/shared/async/useAsyncState";
import AppButton from "@/shared/components/AppButton.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import ErrorState from "@/shared/components/ErrorState.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import type { Payout, PayoutStatement } from "@/shared/domain/Payout";
import type { StudioMember } from "@/shared/domain/StudioMember";
import { useSession } from "@/shared/session/useSession";

/** Repasses semanais (RN-REP-003 a RN-REP-007).
 *
 * A única peça desta pasta que fala com a API; os componentes ao lado recebem
 * tudo por `props`.
 *
 * **O recorte é do backend** (RN-REP-004): o artista recebe só os próprios
 * repasses, o gestor recebe todos. A tela não filtra — num módulo que diz
 * quanto cada pessoa recebeu, duas versões da mesma regra é a última coisa que
 * se quer, e a do navegador seria a que ficaria para trás.
 *
 * **Fechar a semana é do gestor**, e é um ato explícito: a regra manda calcular
 * depois do fechamento de sexta às 20h, e o sistema o faz quando pedem — sem
 * agendador, que é da Fase 2 (ADR-008). Fechar duas vezes devolve o mesmo
 * fechamento.
 *
 * **Confirmar a transferência não transfere nada.** O gestor paga por fora e
 * registra; o sistema nunca move dinheiro sozinho (ADR-029). */
interface PayoutsBoard {
  payouts: Payout[];
  artists: StudioMember[];
}

const { payouts: payoutsApi, accounts } = useApi();
const { session, permissions } = useSession();

const state = useAsyncState<PayoutsBoard>();
const statement = ref<PayoutStatement | null>(null);
const busy = ref(false);
const failure = ref<string | null>(null);

const user = session.user;

const isStaff = computed(() => (user.value ? permissions.isStaff(user.value) : false));

const scopeNote = computed(() =>
  isStaff.value
    ? "Every payout in the studio."
    : "Only your own payouts. The studio management sees all of them.",
);

const heading = computed(() => {
  const total = state.data.value?.payouts.length ?? 0;
  return `${total} payout${total === 1 ? "" : "s"}`;
});

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
    payouts: await payoutsApi.list(),
    artists: await knownArtists(),
  }));
}

/** Só o gestor lista contas. O artista vê os próprios repasses e o nome dele
 * entra pelo mapa acima — sem isso o cartão mostraria "Artist" para quem está
 * olhando a própria tela. */
async function knownArtists(): Promise<StudioMember[]> {
  try {
    return await accounts.listArtists();
  } catch {
    return [];
  }
}

/** Fecha a semana **anterior** à corrente.
 *
 * A semana em curso ainda não terminou, e o backend a recusa — corretamente. O
 * botão oferece a última já encerrada, que é a que o gestor quer fechar numa
 * segunda-feira de manhã. */
async function closeWeek(): Promise<void> {
  const lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  await act(() => payoutsApi.closeWeek(lastWeek.toISOString()));
}

async function open(payout: Payout): Promise<void> {
  failure.value = null;
  try {
    statement.value = await payoutsApi.statement(payout.id);
  } catch (error) {
    failure.value =
      error instanceof ApiError ? error.message : "Could not reach the studio system.";
  }
}

async function confirm(payout: Payout): Promise<void> {
  await act(() => payoutsApi.confirmPaid(payout.id));
  statement.value = null;
}

/** Toda ação passa por aqui: ocupa, limpa o erro anterior, tenta e recarrega. */
async function act(action: () => Promise<unknown>): Promise<void> {
  busy.value = true;
  failure.value = null;
  try {
    await action();
    await load();
  } catch (error) {
    failure.value =
      error instanceof ApiError ? error.message : "Could not reach the studio system.";
  } finally {
    busy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="payouts">
    <PageHeader
      kicker="Studio workspace"
      :title="heading"
    >
      <template #actions>
        <AppButton
          v-if="isStaff"
          :busy="busy"
          :disabled="state.isLoading.value"
          @click="closeWeek"
        >
          Close last week
        </AppButton>
      </template>
    </PageHeader>

    <p class="scope">
      {{ scopeNote }}
    </p>

    <p
      v-if="failure"
      class="failure"
      role="alert"
    >
      {{ failure }}
    </p>

    <LoadingState v-if="state.isLoading.value" />

    <ErrorState
      v-else-if="state.error.value"
      :message="state.errorMessage.value"
      :retryable="state.isRetryable.value"
      @retry="state.retry()"
    />

    <EmptyState
      v-else-if="state.data.value && state.data.value.payouts.length === 0"
      title="No payouts yet"
      description="A week closes every Friday at 20:00. Sessions settled in it are calculated then."
    />

    <PayoutList
      v-else-if="state.data.value"
      :payouts="state.data.value.payouts"
      :artist-names="namesByArtist"
      :can-confirm="isStaff"
      :busy="busy"
      @open="open"
      @confirm="confirm"
    />

    <PayoutStatementModal
      v-if="statement"
      :statement="statement"
      :artist-name="namesByArtist[statement.payout.artistId] ?? 'Artist'"
      :can-confirm="isStaff"
      :busy="busy"
      :failure="failure"
      @confirm="confirm(statement.payout)"
      @close="statement = null"
    />
  </div>
</template>

<style scoped>
.payouts {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.scope {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
