<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import MonthComparison from "@/features/revenue/components/MonthComparison.vue";
import RevenueSummary from "@/features/revenue/components/RevenueSummary.vue";
import RevenueTable from "@/features/revenue/components/RevenueTable.vue";
import { RevenueMonth } from "@/features/revenue/RevenueMonth";
import { useApi } from "@/shared/api/useApi";
import { useAsyncState } from "@/shared/async/useAsyncState";
import AppButton from "@/shared/components/AppButton.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import ErrorState from "@/shared/components/ErrorState.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import type { MonthlyRevenue, RevenueReport } from "@/shared/domain/Revenue";

/** Faturamento do estúdio, mês a mês (RN 10.4).
 *
 * A única peça desta pasta que fala com a API; os componentes ao lado recebem
 * tudo por `props`.
 *
 * É o controle que o estúdio mantinha em planilha, com as mesmas colunas e os
 * mesmos três totais no rodapé — **de propósito**: quem confere o mês já sabe
 * ler aquela tabela.
 *
 * **Só gerente e proprietário** (RN 10.4). O backend recusa os demais com 403 e
 * o item de menu não aparece para eles; o artista vê o que lhe diz respeito na
 * tela de repasses, com o recorte dele (RN-REP-004).
 *
 * **Nada aqui é calculado no navegador.** Divisão, arredondamento e soma vêm do
 * backend, pelo mesmo `PayoutShare` que paga o artista — se esta tela fizesse a
 * própria conta, o estúdio teria dois números para a mesma coisa, e a diferença
 * de um centavo viraria uma conversa que não é sobre software.
 *
 * **O mês e a comparação são duas chamadas**, e não uma. A comparação carrega
 * doze meses de totais; o detalhamento carrega as linhas de um só. Juntá-las
 * traria o ano inteiro de atendimentos para desenhar doze linhas de tabela. */
const { revenue, accounts } = useApi();

const months = new RevenueMonth();
const limit = months.current();

const open = ref(months.current());
const state = useAsyncState<RevenueReport>();
const comparison = ref<MonthlyRevenue[]>([]);
const artistNames = ref<Record<string, string>>({});

const label = computed(() => months.label(open.value.year, open.value.month));

/** Não há faturamento no futuro, e oferecer o mês seguinte levaria o gestor a
 * uma tela vazia que ele leria como defeito. */
const sameAsLimit = computed(
  () => open.value.year === limit.year && open.value.month === limit.month,
);

async function load(): Promise<void> {
  await state.run(() => revenue.month(open.value.year, open.value.month));
}

/** Buscada uma vez e refeita a cada troca de mês: a janela de doze meses é
 * relativa ao mês aberto, e manter a de outubro enquanto se olha julho faria a
 * tabela comparar o mês aberto com meses que não o cercam. */
async function loadComparison(): Promise<void> {
  try {
    comparison.value = await revenue.monthly(open.value.year, open.value.month, 12);
  } catch {
    comparison.value = [];
  }
}

/** Sem o nome, a linha ainda aparece — com o identificador em vez da pessoa. Um
 * atendimento escondido é pior do que um atendimento sem rótulo. */
async function loadArtists(): Promise<void> {
  try {
    const artists = await accounts.listArtists();
    artistNames.value = Object.fromEntries(
      artists.map((artist) => [artist.id, artist.displayName]),
    );
  } catch {
    artistNames.value = {};
  }
}

async function show(year: number, month: number): Promise<void> {
  open.value = { year, month };
  await Promise.all([load(), loadComparison()]);
}

onMounted(async () => {
  await Promise.all([load(), loadComparison(), loadArtists()]);
});
</script>

<template>
  <div class="revenue">
    <PageHeader
      kicker="Studio workspace"
      :title="label"
    >
      <template #actions>
        <AppButton
          tone="ghost"
          :disabled="state.isLoading.value"
          @click="show(months.previous(open.year, open.month).year, months.previous(open.year, open.month).month)"
        >
          Previous month
        </AppButton>
        <AppButton
          tone="ghost"
          :disabled="state.isLoading.value || sameAsLimit"
          @click="show(months.next(open.year, open.month).year, months.next(open.year, open.month).month)"
        >
          Next month
        </AppButton>
      </template>
    </PageHeader>

    <p class="scope">
      Every session the studio has already received the money for. The deposit is
      inside the value, not on top of it — the split applies to the whole.
    </p>

    <LoadingState v-if="state.isLoading.value" />

    <ErrorState
      v-else-if="state.error.value"
      :message="state.errorMessage.value"
      :retryable="state.isRetryable.value"
      @retry="state.retry()"
    />

    <template v-else-if="state.data.value">
      <RevenueSummary
        :totals="state.data.value.totals"
        :period="label"
      />

      <MonthComparison
        v-if="comparison.length > 0"
        :months="comparison"
        :open-year="open.year"
        :open-month="open.month"
        @open="show($event.year, $event.month)"
      />

      <EmptyState
        v-if="state.data.value.lines.length === 0"
        title="Nothing settled in this month"
        description="A session appears here once the studio confirms it received the money."
      />

      <RevenueTable
        v-else
        :lines="state.data.value.lines"
        :artist-names="artistNames"
      />
    </template>
  </div>
</template>

<style scoped>
.revenue {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.scope {
  max-width: var(--content-measure);
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
