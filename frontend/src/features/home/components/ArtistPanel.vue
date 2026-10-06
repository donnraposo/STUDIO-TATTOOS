<script setup lang="ts">
import { computed } from "vue";

import { ArtistBoard } from "@/features/home/ArtistBoard";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Booking } from "@/shared/domain/Booking";
import type { Payout } from "@/shared/domain/Payout";
import type { Quote } from "@/shared/domain/Quote";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";
import { StudioClock } from "@/shared/format/StudioClock";

/** O painel de quem tatua (seções 10.2 e 10.3).
 *
 * Responde às três perguntas do artista ao abrir o sistema: o que tenho hoje, o
 * que estou esperando o estúdio decidir, e quanto entrou no último fechamento.
 *
 * **O recorte é do backend.** O artista vê a própria agenda, os próprios
 * orçamentos e os próprios repasses porque o servidor devolve só isso — não
 * porque esta tela filtra. Refiltrar aqui daria duas versões das regras
 * RN-CLI-004 e RN-REP-004, e a do navegador seria a que ficaria para trás.
 *
 * **Orçamentos só aparecem para quem os tem.** O guest não acessa o módulo
 * (RN-ORC-001), e um cartão vazio dizendo "0 quotes" lhe prometeria uma tela
 * que o servidor recusa.
 *
 * **O repasse mostrado é o último fechado, e o rótulo diz isso.** Não há
 * previsão da semana corrente: ela só existe depois do fechamento de sexta às
 * 20h (RN-REP-004), e um número adiantado seria o sistema dizendo ao artista
 * quanto ele vai receber sem que ninguém tenha fechado nada.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  bookings: Booking[];
  quotes: Quote[];
  payouts: Payout[];
  clientNames: Record<string, string>;
  showQuotes: boolean;
  now: string;
}>();

defineEmits<{ open: [route: string] }>();

const board = new ArtistBoard();
const clock = new StudioClock();
const money = new MoneyFormatter();

const day = computed(() => board.today(props.bookings));
const next = computed(() => board.next(props.bookings, props.now));
const waiting = computed(() => board.awaitingDecision(props.bookings));
const quotesPending = computed(() => board.quotesPending(props.quotes));
const payout = computed(() => board.lastPayout(props.payouts));

function clientOf(booking: Booking): string {
  return props.clientNames[booking.clientId] ?? "Client";
}
</script>

<template>
  <section class="panel">
    <SectionKicker label="Your day" />
    <h2>
      {{ day.length }} booking{{ day.length === 1 ? "" : "s" }} today
    </h2>

    <EmptyState
      v-if="day.length === 0"
      title="Nothing on the bench today"
      description="Your approved bookings and the requests still waiting show up here."
    />

    <ul
      v-else
      class="day"
    >
      <li
        v-for="booking in day"
        :key="booking.id"
        :class="{ 'is-next': next?.id === booking.id }"
      >
        <span class="hour">
          {{ clock.time(booking.startsAt) }}–{{ clock.time(booking.endsAt) }}
        </span>
        <span class="client">{{ clientOf(booking) }}</span>
        <StatusBadge
          v-if="booking.status === 'REQUESTED'"
          label="Awaiting decision"
          tone="warning"
        />
      </li>
    </ul>

    <div class="cards">
      <AppCard title="Waiting on the studio">
        <p class="figure">
          {{ waiting }}
        </p>
        <p class="caption">
          {{ waiting === 1 ? "booking request" : "booking requests" }} not decided yet
        </p>
        <template #footer>
          <AppButton
            tone="ghost"
            @click="$emit('open', 'schedule')"
          >
            Open schedule
          </AppButton>
        </template>
      </AppCard>

      <AppCard
        v-if="props.showQuotes"
        title="Quotes"
      >
        <p class="figure">
          {{ quotesPending }}
        </p>
        <p class="caption">
          {{ quotesPending === 1 ? "quote" : "quotes" }} still to be approved
        </p>
        <template #footer>
          <AppButton
            tone="ghost"
            @click="$emit('open', 'quotes')"
          >
            Open quotes
          </AppButton>
        </template>
      </AppCard>

      <AppCard title="Last payout">
        <p class="figure">
          {{ money.amount(payout?.netTotal) }}
        </p>
        <p class="caption">
          <template v-if="payout">
            week closed {{ clock.date(payout.periodEnd) }}
          </template>
          <template v-else>
            nothing closed yet — a week closes every Friday at 20:00
          </template>
        </p>
        <template #footer>
          <AppButton
            tone="ghost"
            @click="$emit('open', 'payouts')"
          >
            Open payouts
          </AppButton>
        </template>
      </AppCard>
    </div>
  </section>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

h2 {
  margin: var(--space-0);
  font-size: var(--text-heading-2);
  font-weight: var(--weight-regular);
}

.day {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

.day li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

/* O que vem agora ganha a borda: numa lista de seis horários, saber qual é o
   próximo é a pergunta que se faz ao abrir a tela. */
.day li.is-next {
  border-left: var(--border-dark);
}

.hour {
  font-weight: var(--weight-medium);
}

.client {
  flex: 1;
  color: var(--color-muted);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--track-card-min), 1fr));
  gap: var(--space-4);
}

.figure {
  margin: var(--space-0);
  font-size: var(--text-heading-1);
  line-height: var(--line-tight);
}

.caption {
  margin: var(--space-0);
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
