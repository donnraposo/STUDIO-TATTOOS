<script setup lang="ts">
import AppCard from "@/shared/components/AppCard.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { RevenueLine } from "@/shared/domain/Revenue";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";
import { StudioClock } from "@/shared/format/StudioClock";

/** O detalhamento do mês, atendimento por atendimento.
 *
 * É a planilha que o estúdio mantinha à mão, com as mesmas colunas e na mesma
 * ordem — **de propósito**: quem confere o mês já sabe ler esta tabela, e
 * reorganizá-la obrigaria a reaprender o que já se sabe.
 *
 * **O percentual aparece em cada linha**, e não só o valor. O mesmo artista
 * aparece em divisões diferentes no mesmo mês (RN-CLI-003 e ADR-030), e sem a
 * coluna a comissão pareceria errada em metade das linhas.
 *
 * O nome do artista chega pronto, por `props`: cruzar identificadores é
 * trabalho da tela, e assim este componente continua sem conhecer a API.
 *
 * Componente de apresentação: recebe por `props`, não emite nada. */
const props = defineProps<{
  lines: RevenueLine[];
  artistNames: Record<string, string>;
}>();

const money = new MoneyFormatter();
const clock = new StudioClock();
</script>

<template>
  <AppCard title="Every session">
    <div class="scroller">
      <table>
        <thead>
          <tr>
            <th scope="col">
              Date
            </th>
            <th scope="col">
              Artist
            </th>
            <th scope="col">
              Value
            </th>
            <th scope="col">
              Artist
            </th>
            <th scope="col">
              Studio
            </th>
            <th scope="col">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="line in props.lines"
            :key="line.sessionId"
          >
            <td>{{ clock.date(line.settledAt) }}</td>
            <td class="who">
              {{ props.artistNames[line.artistId] ?? "Artist" }}
            </td>
            <td>{{ money.amount(line.value) }}</td>
            <td>
              {{ money.amount(line.artistAmount) }}
              <small>{{ money.percentage(line.percentage) }}</small>
            </td>
            <td>{{ money.amount(line.studioAmount) }}</td>
            <td>
              <StatusBadge
                :label="line.transferred ? 'Paid' : 'Not paid yet'"
                :tone="line.transferred ? 'positive' : 'neutral'"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </AppCard>
</template>

<style scoped>
/* A tabela tem seis colunas e nao encolhe abaixo de certo ponto sem ficar
   ilegivel: no celular ela rola na horizontal em vez de espremer numeros. */
.scroller {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: var(--space-3) var(--space-3);
  border-bottom: var(--border-thin);
  text-align: right;
  white-space: nowrap;
}

th:first-child,
td:first-child,
.who {
  text-align: left;
}

th {
  color: var(--color-muted);
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
}

td small {
  display: block;
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
