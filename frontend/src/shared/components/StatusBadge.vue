<script setup lang="ts">
/** Selo de estado.
 *
 * O tom vem por mapa tipado. Quando a M7.1.3 acrescentar os estados de
 * agendamento e a M7.1.4 os de orçamento, cada um é uma entrada de dados na
 * tela que o usa — nada muda aqui dentro. */
type BadgeTone = "neutral" | "positive" | "danger" | "warning" | "info";

const TONE_CLASS: Record<BadgeTone, string> = {
  neutral: "is-neutral",
  positive: "is-positive",
  danger: "is-danger",
  warning: "is-warning",
  info: "is-info",
};

const props = withDefaults(defineProps<{ label: string; tone?: BadgeTone }>(), {
  tone: "neutral",
});
</script>

<template>
  <span
    class="badge"
    :class="TONE_CLASS[props.tone]"
  >{{ props.label }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-round);
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.is-neutral {
  background: var(--color-surface-soft);
  color: var(--color-muted);
}

.is-positive {
  background: var(--color-positive-soft);
  color: var(--color-positive);
}

.is-danger {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.is-warning {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.is-info {
  background: var(--color-info-soft);
  color: var(--color-info);
}
</style>
