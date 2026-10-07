<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { AccountManagementReach } from "@/features/accounts/AccountManagementReach";
import AccountFormModal, {
  type AccountDraft,
} from "@/features/accounts/components/AccountFormModal.vue";
import AccountList from "@/features/accounts/components/AccountList.vue";
import ArtistShareModal from "@/features/accounts/components/ArtistShareModal.vue";
import BlockAccountModal from "@/features/accounts/components/BlockAccountModal.vue";
import { ApiError } from "@/shared/api/ApiError";
import { useApi } from "@/shared/api/useApi";
import { useAsyncState } from "@/shared/async/useAsyncState";
import AppButton from "@/shared/components/AppButton.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import ErrorState from "@/shared/components/ErrorState.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import type { StudioAccount } from "@/shared/domain/StudioAccount";
import { useSession } from "@/shared/session/useSession";

/** Contas e artistas do estúdio (RN 2.1 a 2.6 e ADR-030).
 *
 * A única peça desta pasta que fala com a API; os componentes ao lado recebem
 * tudo por `props`.
 *
 * **Só gerente e proprietário entram** — o backend recusa os demais com 403 ao
 * listar, e o item de menu não aparece para eles. A tela não repete a
 * verificação para decidir o que carregar: ela pede, e mostra o que voltar.
 *
 * **O percentual mora aqui porque é acordo da pessoa, não do atendimento.** O
 * estúdio opera com mais de uma divisão ao mesmo tempo, e até esta tela existir
 * só havia dois valores fixos no código — acrescentar um terceiro exigia uma
 * versão nova do sistema. Corrigir o percentual de **um** atendimento continua
 * sendo na aprovação do orçamento (RN-CLI-003), e o que é decidido lá tem
 * precedência sobre o que é decidido aqui.
 *
 * **Não há exclusão de conta**, de propósito: apagar quem assinou um
 * atendimento apagaria o atendimento. Bloquear encerra o acesso e preserva o
 * histórico (RN 2.5). */
const { accounts: accountsApi } = useApi();
const { session } = useSession();

const state = useAsyncState<StudioAccount[]>();
const reach = new AccountManagementReach();

/** Nulo e fechado são estados diferentes: `editing` guarda a conta aberta,
 * e `creating` liga o mesmo formulário sem conta nenhuma. */
const creating = ref(false);
const editing = ref<StudioAccount | null>(null);
const sharing = ref<StudioAccount | null>(null);
const blocking = ref<StudioAccount | null>(null);
const busy = ref(false);
const failure = ref<string | null>(null);

const actor = session.user;

const heading = computed(() => {
  const total = state.data.value?.length ?? 0;
  return `${total} account${total === 1 ? "" : "s"}`;
});

const creatableRoles = computed(() =>
  actor.value ? reach.creatableRoles(actor.value) : [],
);

async function load(): Promise<void> {
  await state.run(() => accountsApi.listAll());
}

async function create(draft: AccountDraft): Promise<void> {
  await act(
    () => accountsApi.create({ ...draft, password: draft.password ?? "" }),
    () => (creating.value = false),
  );
}

/** Ato separado do `salvar`, de propósito (RN 2.7): definir uma senha encerra
 * as sessões da conta, e junto com os demais campos o gestor derrubaria alguém
 * ao corrigir um telefone. O modal continua aberto — quem acabou de dar a senha
 * nova costuma ter mais o que arrumar ali. */
async function setPassword(password: string): Promise<void> {
  const account = editing.value;
  if (account) {
    await act(() => accountsApi.setPassword(account.id, password));
  }
}

async function save(draft: AccountDraft): Promise<void> {
  const account = editing.value;
  if (account) {
    await act(() => accountsApi.update(account.id, draft), () => (editing.value = null));
  }
}

async function setShare(percentage: string | null): Promise<void> {
  const account = sharing.value;
  if (account) {
    await act(
      () => accountsApi.setPercentage(account.id, percentage),
      () => (sharing.value = null),
    );
  }
}

async function block(reason: string): Promise<void> {
  const account = blocking.value;
  if (account) {
    await act(() => accountsApi.block(account.id, reason), () => (blocking.value = null));
  }
}

async function unblock(account: StudioAccount): Promise<void> {
  await act(() => accountsApi.unblock(account.id));
}

/** Toda ação passa por aqui: ocupa, limpa o erro anterior, tenta, recarrega e
 * só então fecha o que estava aberto.
 *
 * Fechar antes de recarregar devolveria o gestor a uma lista com o valor
 * antigo; fechar quando a chamada falha esconderia dele o motivo. */
async function act(action: () => Promise<unknown>, done?: () => void): Promise<void> {
  busy.value = true;
  failure.value = null;
  try {
    await action();
    await load();
    done?.();
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
  <div class="accounts">
    <PageHeader
      kicker="Studio workspace"
      :title="heading"
    >
      <template #actions>
        <AppButton
          v-if="creatableRoles.length > 0"
          :disabled="state.isLoading.value"
          @click="creating = true"
        >
          New account
        </AppButton>
      </template>
    </PageHeader>

    <p class="scope">
      Roles, access and the share agreed with each artist. A share of
      <strong>By origin</strong> means the artist follows the standard rule —
      70% on their own clients, 50% on studio referrals.
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
      v-else-if="state.data.value && state.data.value.length === 0"
      title="No accounts yet"
      description="Every artist and manager who works at the studio needs one."
    />

    <AccountList
      v-else-if="state.data.value && actor"
      :accounts="state.data.value"
      :actor="actor"
      :busy="busy"
      @edit="editing = $event"
      @set-share="sharing = $event"
      @block="blocking = $event"
      @unblock="unblock"
    />

    <AccountFormModal
      v-if="creating"
      :account="null"
      :roles="creatableRoles"
      :can-change-role="true"
      :busy="busy"
      :failure="failure"
      @submit="create"
      @close="creating = false"
    />

    <AccountFormModal
      v-if="editing"
      :account="editing"
      :roles="creatableRoles"
      :can-change-role="actor ? reach.canChangeRole(actor) : false"
      :busy="busy"
      :failure="failure"
      @submit="save"
      @set-password="setPassword"
      @close="editing = null"
    />

    <ArtistShareModal
      v-if="sharing"
      :account="sharing"
      :busy="busy"
      :failure="failure"
      @save="setShare"
      @close="sharing = null"
    />

    <BlockAccountModal
      v-if="blocking"
      :account="blocking"
      :busy="busy"
      :failure="failure"
      @confirm="block"
      @close="blocking = null"
    />
  </div>
</template>

<style scoped>
.accounts {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.scope {
  max-width: var(--content-measure);
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
