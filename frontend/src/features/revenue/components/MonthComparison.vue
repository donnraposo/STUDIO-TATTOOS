<script setup lang="ts">
import { computed } from "vue";

import { RevenueBars } from "@/features/revenue/RevenueBars";
import { RevenueMonth } from "@/features/revenue/RevenueMonth";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import type { MonthlyRevenue } from "@/shared/domain/Revenue";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Como os meses se comparam (RN 10.4).
 *
 * **Tabela e não gráfico de barras**, e a razão é o que se compara: o estúdio
 * quer ver o total, o que foi para os tatuadores e o que ficou com a casa, mês
 * a mês. Barras mostram **um** número por mês; para mostrar três seriam três
 * gráficos, ou um gráfico que ninguém lê. A barra continua existindo, deitada,
 * ao lado do número — dá a proporção sem substituir o valor.
 *
 * **Cada mês abre**, e é o que o estúdio pediu: ver a movimentação de um mês
 * passado sem procurar por ele.
 *
 * A escala é relativa ao maior mês do período, não a um teto fixo — o estúdio
 * compara meses entre si, e um eixo absoluto faria todos parecerem iguais num
 * ano fraco. A geometria mora no `RevenueBars`, testável sem montar a tela.
 *
 * **Mês zerado continua na tabela**, com barra de largura zero. Sumir com ele
 * faria a comparação mentir sobre o tempo: um mês vazio é informação, e um mês
 * ausente faz parecer que o anterior foi ontem.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  months: MonthlyRevenue[];
  openYear: number;
  openMonth: number;
}>();

defineEmits<{ open: [month: MonthlyRevenue] }>();

const bars = new RevenueBars();
const calendar = new RevenueMonth();
const money = new MoneyFormatter();

const widths = computed(() => bars.heights(props.months));

function isOpen(month: MonthlyRevenue): boolean {
  return month.year === props.openYear && month.month === props.openMonth;
}
</script>

<template>
  <AppCard title="Month by month">
    <div class="scroller">
      <table>
        <thead>
          <tr>
            <th scope="col">
              Month
            </th>
            <th scope="col">
              Tattooed
            </th>
            <th scope="col">
              Artists
            </th>
            <th scope="col">
              Studio
            </th>
            <th scope="col">
              Detail
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(month, index) in props.months"
            :key="`${month.year}-${month.month}`"
            :class="{ 'is-open': isOpen(month) }"
          >
            <th scope="row">
              {{ calendar.shortLabel(month.year, month.month) }} {{ month.year }}
            </th>
            <td>
              <span class="value">{{ money.amount(month.totals.value) }}</span>
              <span class="track">
                <span
                  class="bar"
                  :style="{ width: `${widths[index]}%` }"
                />
              </span>
            </td>
            <td>{{ money.amount(month.totals.artists) }}</td>
            <td class="studio">
              {{ money.amount(month.totals.studio) }}
            </td>
            <td>
              <AppButton
                v-if="!isOpen(month)"
                tone="ghost"
                @click="$emit('open', month)"
              >
                Open
              </AppButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </AppCard>
</template>

<style scoped>
.scroller {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: var(--space-3);
  border-bottom: var(--border-thin);
  text-align: right;
  white-space: nowrap;
}

thead th,
tbody th {
  color: var(--color-muted);
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
}

tbody th {
  color: var(--color-on-light);
  text-align: left;
}

/* O mes aberto fica marcado: sem isso a tabela nao diz qual deles o
   detalhamento abaixo esta explicando. */
tr.is-open {
  background: var(--color-surface-soft);
}

.value {
  display: block;
}

.track {
  display: block;
  width: var(--chart-bar-width);
  margin-left: auto;
  margin-top: var(--space-1);
}

.bar {
  display: block;
  height: var(--chart-bar-height);
  border-radius: var(--radius-sm);
  background: var(--gradient-gold);
  transition: width var(--transition-slow);
}

.studio {
  color: var(--color-gold-deep);
  font-weight: var(--weight-medium);
}
</style>
