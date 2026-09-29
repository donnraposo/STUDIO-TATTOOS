<script setup lang="ts">
import { computed } from "vue";

import BookingBlock from "@/features/scheduling/components/BookingBlock.vue";
import type { BookingPlacement, Placement } from "@/features/scheduling/BookingPlacement";
import type { Booking, Booth } from "@/shared/domain/Booking";

/** A timeline: macas no eixo Y, horas no eixo X (ADR-004).
 *
 * Grade em CSS Grid, sem biblioteca. O posicionamento não é calculado aqui —
 * vem do `BookingPlacement`, que é classe pura e testada. Este componente
 * desenha.
 *
 * **Uma linha de grade por maca, e não uma lista por maca.** Com linhas
 * independentes, duas macas deixariam de compartilhar o eixo do tempo assim
 * que uma tivesse rolagem própria, e a leitura "o que está acontecendo às 14h"
 * — que é a razão de a tela existir — se perderia. */
interface PlacedBooking {
  booking: Booking;
  placement: Placement;
  clientName: string;
  timeRange: string;
  track: number;
}

const props = defineProps<{
  booths: Booth[];
  placer: BookingPlacement;
  placedByBooth: Record<string, PlacedBooking[]>;
  tracksByBooth: Record<string, number>;
}>();

defineEmits<{ select: [booking: Booking] }>();

const gridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${props.placer.slotCount}, minmax(var(--slot-width), 1fr))`,
}));

/** A maca cresce em altura quando há solicitações concorrentes: cada trilha é
 * uma linha da grade, e todas ficam visíveis (RN-AGE-004). */
function laneStyle(boothId: string): Record<string, string> {
  return {
    ...gridStyle.value,
    gridTemplateRows: `repeat(${props.tracksByBooth[boothId] ?? 1}, auto)`,
  };
}

/** A maca e identificada pelo numero, so (RN-AGE-001).
 *
 * O modelo tem um campo `label`, mas nenhuma regra pede apelido de maca, e
 * mostrar "Window" ao lado do numero convida cada pessoa a inventar o seu --
 * ate duas macas terem nomes que so uma parte da equipe reconhece. */
function boothName(booth: Booth): string {
  return `Booth ${booth.number}`;
}
</script>

<template>
  <div class="timeline">
    <div class="scroller">
      <div class="head">
        <span class="corner" />
        <div
          class="hours"
          :style="gridStyle"
        >
          <span
            v-for="label in placer.hourLabels"
            :key="label"
            class="hour"
          >
            {{ label }}
          </span>
        </div>
      </div>

      <div
        v-for="booth in booths"
        :key="booth.id"
        class="lane"
      >
        <span class="booth">{{ boothName(booth) }}</span>
        <div
          class="slots"
          :style="laneStyle(booth.id)"
        >
          <BookingBlock
            v-for="placed in placedByBooth[booth.id] ?? []"
            :key="placed.booking.id"
            :booking="placed.booking"
            :placement="placed.placement"
            :client-name="placed.clientName"
            :time-range="placed.timeRange"
            :track="placed.track"
            @select="$emit('select', $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  overflow: hidden;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

/* A rolagem é do conjunto, nunca de uma linha só: as macas precisam continuar
   compartilhando o mesmo eixo de tempo. */
.scroller {
  overflow-x: auto;
  padding: var(--space-4);
}

.head,
.lane {
  display: grid;
  grid-template-columns: var(--lane-label-width) 1fr;
  gap: var(--space-3);
  align-items: center;
  min-width: fit-content;
}

.head {
  padding-bottom: var(--space-3);
  border-bottom: var(--border-thin);
}

.hours,
.slots {
  display: grid;
  gap: var(--space-1);
}

/* Um rótulo a cada duas faixas de trinta minutos, ou seja, de hora em hora. */
.hour {
  grid-column: span 2;
  color: var(--color-muted);
  font-size: var(--text-kicker);
  letter-spacing: var(--tracking-kicker);
}

.lane {
  padding: var(--space-2) var(--space-0);
  border-bottom: var(--border-thin);
}

.lane:last-child {
  border-bottom: none;
}

/* Sem listras de fundo: o cabecalho de horas e a divisao entre macas ja dao a
   estrutura, e a referencia de design e espacosa. Listras a cada trinta minutos
   competiriam com os proprios blocos, que sao o conteudo. */
.slots {
  min-height: var(--touch-target);
}

.booth {
  color: var(--color-on-light);
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
}

/* No celular a coluna de macas encolhe e o respiro diminui: 9rem de rotulo
   comeriam um quarto da largura util antes de qualquer horario aparecer. A
   grade continua rolando na horizontal, que e o comportamento certo aqui --
   comprimir o dia inteiro na tela tornaria os blocos ilegiveis. */
@media (max-width: 40rem) {
  .head,
  .lane {
    grid-template-columns: var(--lane-label-width-compact) 1fr;
    gap: var(--space-2);
  }

  .scroller {
    padding: var(--space-3);
  }
}
</style>
