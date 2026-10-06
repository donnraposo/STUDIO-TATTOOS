<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import PaymentList from "@/features/payments/components/PaymentList.vue";
import RefundPaymentModal, {
  type RefundDraft,
} from "@/features/payments/components/RefundPaymentModal.vue";
import RefusePaymentModal from "@/features/payments/components/RefusePaymentModal.vue";
import { ApiError } from "@/shared/api/ApiError";
import { useApi } from "@/shared/api/useApi";
import { useAsyncState } from "@/shared/async/useAsyncState";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import ErrorState from "@/shared/components/ErrorState.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import type { Payment, PaymentStatus } from "@/shared/domain/Payment";
import { useSession } from "@/shared/session/useSession";

/** Pagamentos do estúdio (RN-PAG-002, RN-PAG-007 e RN-PAG-009).
 *
 * A única peça desta pasta que fala com a API; os componentes ao lado recebem
 * tudo por `props`.
 *
 * **Abre no que espera decisão**, e não no histórico: um recebimento informado
 * e não conferido trava a aprovação do horário (RN-AGE-005), e é a única coisa
 * desta tela com consequência em outra. O histórico está a um seletor de
 * distância, para quando a pergunta for outra.
 *
 * **Aqui não se registra pagamento, e isso é desenho.** Um recebimento pertence
 * ou ao agendamento ou à sessão, nunca a nenhum dos dois: o sinal confirma o
 * horário reservado (RN-PAG-001), o saldo quita a sessão (RN-PAG-008). Lançar a
 * partir daqui obrigaria o gestor a procurar o agendamento numa lista para
 * dizer ao sistema de onde veio o dinheiro — então o lançamento mora onde a
 * origem já é conhecida: o sinal no agendamento, o saldo na sessão.
 *
 * **Nenhum botão daqui movimenta dinheiro** (ADR-029 e RN-PAG-006). Confirmar é
 * escrituração de algo que já entrou; devolver é registro de algo que o gestor
 * já devolveu por fora. */
const FILTERS: SelectOption[] = [
  { value: "REPORTED", label: "Awaiting confirmation" },
  { value: "CONFIRMED", label: "Confirmed" },
  { value: "REFUSED", label: "Refused" },
  { value: "REFUNDED", label: "Refunded" },
  { value: "CHARGED_BACK", label: "Charged back" },
];

interface PaymentsBoard {
  payments: Payment[];
  clientNames: Record<string, string>;
}

const { payments: paymentsApi, clients } = useApi();
const { session, permissions } = useSession();

const state = useAsyncState<PaymentsBoard>();
const filter = ref<string>("REPORTED");
const refusing = ref<Payment | null>(null);
const refunding = ref<Payment | null>(null);
const busy = ref(false);
const failure = ref<string | null>(null);

const user = session.user;

const canDecide = computed(() => (user.value ? permissions.canDecide(user.value) : false));

const heading = computed(() => {
  const total = state.data.value?.payments.length ?? 0;
  return `${total} payment${total === 1 ? "" : "s"}`;
});

const emptyMessage = computed(() =>
  filter.value === "REPORTED"
    ? "Nothing is waiting for you to confirm a receipt."
    : "No payment in this state.",
);

async function load(): Promise<void> {
  await state.run(async () => ({
    payments: await paymentsApi.listByStatus(filter.value as PaymentStatus),
    clientNames: await names(),
  }));
}

/** Sem o nome, o pagamento ainda aparece — com o identificador em vez da
 * pessoa. Um recebimento escondido é pior do que um recebimento sem rótulo. */
async function names(): Promise<Record<string, string>> {
  try {
    const list = await clients.list();
    return Object.fromEntries(list.map((client) => [client.id, client.name]));
  } catch {
    return {};
  }
}

async function confirm(payment: Payment): Promise<void> {
  await act(() => paymentsApi.confirm(payment.id));
}

async function refuse(reason: string): Promise<void> {
  const payment = refusing.value;
  if (payment) {
    await act(() => paymentsApi.refuse(payment.id, reason), () => (refusing.value = null));
  }
}

async function refund(draft: RefundDraft): Promise<void> {
  const payment = refunding.value;
  if (payment) {
    await act(() => paymentsApi.refund(payment.id, draft), () => (refunding.value = null));
  }
}

/** Toda ação passa por aqui: ocupa, limpa o erro anterior, tenta, recarrega e
 * só então fecha o que estava aberto. Fechar antes de recarregar devolveria o
 * gestor a uma lista com o estado antigo; fechar quando falha esconderia dele o
 * motivo. */
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

watch(filter, load);
onMounted(load);
</script>

<template>
  <div class="payments">
    <PageHeader
      kicker="Studio workspace"
      :title="heading"
    >
      <template #actions>
        <AppSelect
          v-model="filter"
          label="State"
          :options="FILTERS"
          :disabled="state.isLoading.value"
        />
      </template>
    </PageHeader>

    <p class="scope">
      A deposit is registered on the booking it confirms, and a balance on the
      session it settles. Nothing here moves money — confirming records what
      arrived, refunding records what you already sent back.
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
      v-else-if="state.data.value && state.data.value.payments.length === 0"
      title="Nothing here"
      :description="emptyMessage"
    />

    <PaymentList
      v-else-if="state.data.value"
      :payments="state.data.value.payments"
      :client-names="state.data.value.clientNames"
      :can-decide="canDecide"
      :busy="busy"
      @confirm="confirm"
      @refuse="refusing = $event"
      @refund="refunding = $event"
    />

    <RefusePaymentModal
      v-if="refusing"
      :payment="refusing"
      :busy="busy"
      :failure="failure"
      @confirm="refuse"
      @close="refusing = null"
    />

    <RefundPaymentModal
      v-if="refunding"
      :payment="refunding"
      :busy="busy"
      :failure="failure"
      @confirm="refund"
      @close="refunding = null"
    />
  </div>
</template>

<style scoped>
.payments {
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
