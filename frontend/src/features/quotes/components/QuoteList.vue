<script setup lang="ts">
import { QuoteDisplay } from "@/features/quotes/QuoteDisplay";
import AppCard from "@/shared/components/AppCard.vue";
import AppButton from "@/shared/components/AppButton.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Quote } from "@/shared/domain/Quote";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** Os orçamentos visíveis a quem está olhando.
 *
 * **Não filtra nada.** O backend já devolve o recorte certo — o gestor vê
 * todos, o artista vê os seus (RN-ORC-001) —, e repetir a regra aqui daria duas
 * versões dela, com a do navegador ficando para trás em silêncio.
 *
 * Os nomes de cliente e artista chegam prontos, por `props`: cruzar
 * identificadores é trabalho da tela, que já consome as duas listas. Assim este
 * componente continua sem conhecer a API.
 *
 * O cartão inteiro não é clicável: só o botão abre o orçamento. Uma superfície
 * grande que reage ao clique é fácil de acionar sem querer num telefone, e o
 * que está do outro lado é um formulário com decisão de dinheiro. */
const props = defineProps<{
  quotes: Quote[];
  clientNames: Record<string, string>;
  artistNames: Record<string, string>;
}>();

defineEmits<{ open: [quote: Quote] }>();

const display = new QuoteDisplay();
const money = new MoneyFormatter();
</script>

<template>
  <ul class="list">
    <li
      v-for="quote in props.quotes"
      :key="quote.id"
    >
      <AppCard>
        <template #header>
          <div class="who">
            <strong>{{ props.clientNames[quote.clientId] ?? "Client" }}</strong>
            <small>{{ props.artistNames[quote.artistId] ?? "Artist" }}</small>
          </div>
          <StatusBadge
            :label="display.status(quote.status).label"
            :tone="display.status(quote.status).tone"
          />
        </template>

        <p class="description">
          {{ quote.description }}
        </p>

        <dl class="numbers">
          <div>
            <dt>Total</dt>
            <dd>{{ money.amount(quote.totalValue) }}</dd>
          </div>
          <div>
            <dt>Sessions</dt>
            <dd>{{ quote.plannedSessions }} × {{ money.amount(quote.plannedValuePerSession) }}</dd>
          </div>
          <div>
            <dt>Origin</dt>
            <dd>{{ display.origin(quote.origin) }}</dd>
          </div>
          <div>
            <dt>Artist share</dt>
            <dd>{{ money.percentage(quote.artistPercentage) }}</dd>
          </div>
        </dl>

        <template #footer>
          <AppButton
            tone="ghost"
            @click="$emit('open', quote)"
          >
            Open
          </AppButton>
        </template>
      </AppCard>
    </li>
  </ul>
</template>

<style scoped>
.list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--track-card-min), 1fr));
  gap: var(--space-4);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

.who {
  display: flex;
  flex-direction: column;
}

.who strong {
  font-weight: var(--weight-medium);
}

.who small {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

/* A descrição pode ter parágrafos; no cartão ela é chamariz, não leitura. Três
   linhas dão o assunto sem deixar um cartão dez vezes mais alto que o vizinho. */
.description {
  display: -webkit-box;
  overflow: hidden;
  color: var(--color-muted);
  font-size: var(--text-label-3);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.numbers {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  margin: var(--space-0);
}

dt {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

dd {
  margin: var(--space-0);
}
</style>
