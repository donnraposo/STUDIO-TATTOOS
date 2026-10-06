<script setup lang="ts">
import AppCard from "@/shared/components/AppCard.vue";
import type { RevenueTotals } from "@/shared/domain/Revenue";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Os três números do rodapé da planilha, no topo da tela.
 *
 * **A ordem é a da conta**: o que entrou, o que saiu para os artistas, o que
 * ficou. Lida da esquerda para a direita, ela se explica sozinha — e é
 * exatamente a conferência que o estúdio faz no fim do mês, porque os dois
 * últimos somam o primeiro.
 *
 * A parte do estúdio ganha o destaque porque é a pergunta que traz o
 * proprietário a esta tela.
 *
 * Componente de apresentação: recebe por `props`, não emite nada. */
const props = defineProps<{ totals: RevenueTotals; period: string }>();

const money = new MoneyFormatter();
</script>

<template>
  <div class="summary">
    <AppCard title="Total tattooed">
      <p class="figure">
        {{ money.amount(props.totals.value) }}
      </p>
      <p class="caption">
        {{ props.totals.sessions }}
        {{ props.totals.sessions === 1 ? "session" : "sessions" }} in {{ props.period }}
      </p>
    </AppCard>

    <AppCard title="Paid to artists">
      <p class="figure">
        {{ money.amount(props.totals.artists) }}
      </p>
      <p class="caption">
        commission on the work above
      </p>
    </AppCard>

    <AppCard title="Studio share">
      <p class="figure is-studio">
        {{ money.amount(props.totals.studio) }}
      </p>
      <p class="caption">
        what the studio kept
      </p>
    </AppCard>
  </div>
</template>

<style scoped>
.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(var(--track-card-min), 1fr));
  gap: var(--space-4);
}

.figure {
  margin: var(--space-0);
  font-size: var(--text-heading-1);
  line-height: var(--line-tight);
}

/* A parte da casa e a pergunta que traz o proprietario aqui. */
.is-studio {
  color: var(--color-gold-deep);
}

.caption {
  margin: var(--space-0);
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
