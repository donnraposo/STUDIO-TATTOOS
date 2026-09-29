<script setup lang="ts">
import type { Placement } from "@/features/scheduling/BookingPlacement";
import type { Booking } from "@/shared/domain/Booking";

/** Um agendamento posicionado na grade.
 *
 * O tom vem de mapa tipado: acrescentar um estado é uma linha de dados. E os
 * tons **não** são decoração — `REQUESTED` e `APPROVED` precisam parecer
 * diferentes porque significam coisas diferentes na maca: pendente não a
 * bloqueia para outro artista, aprovado bloqueia (RN-AGE-004).
 *
 * Não busca nada e não sabe quem está logado: recebe posição e rótulos prontos. */
const STATUS_CLASS: Record<string, string> = {
  REQUESTED: "is-requested",
  APPROVED: "is-approved",
  DONE: "is-done",
  NO_SHOW: "is-no-show",
  REJECTED: "is-inactive",
  CANCELLED: "is-inactive",
};

defineProps<{
  booking: Booking;
  placement: Placement;
  clientName: string;
  timeRange: string;
}>();

defineEmits<{ select: [booking: Booking] }>();
</script>

<template>
  <button
    type="button"
    class="block"
    :class="[STATUS_CLASS[booking.status] ?? 'is-inactive', { 'is-clipped': placement.clipped }]"
    :style="{ gridColumn: `${placement.column} / span ${placement.span}` }"
    :title="`${clientName} · ${timeRange}`"
    @click="$emit('select', booking)"
  >
    <span class="who">{{ clientName }}</span>
    <span class="when">{{ timeRange }}</span>
  </button>
</template>

<style scoped>
.block {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  overflow: hidden;
  width: 100%;
  min-height: var(--touch-target);
  padding: var(--space-2) var(--space-3);
  border: none;
  border-left: var(--border-thin);
  border-radius: var(--radius-sm);
  text-align: left;
}

.who {
  overflow: hidden;
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.when {
  font-size: var(--text-kicker);
  opacity: var(--opacity-disabled);
}

/* Pendente: contorno, sem preenchimento. A maca continua disponível para outro
   artista, e o bloco precisa parecer menos "ocupado" que um aprovado. */
.is-requested {
  border: var(--border-thin);
  border-color: var(--color-warning);
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.is-approved {
  background: var(--color-ink);
  color: var(--color-on-dark);
}

.is-done {
  background: var(--color-positive-soft);
  color: var(--color-positive);
}

.is-no-show {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.is-inactive {
  background: var(--color-surface-soft);
  color: var(--color-muted);
  text-decoration: line-through;
}

/* Sessão que atravessa a borda do expediente: a listra avisa que há mais fora
   da vista, em vez de deixar o bloco mentir sobre a duração. */
.is-clipped {
  border-left: var(--border-dark);
  border-left-color: var(--color-gold);
}
</style>
