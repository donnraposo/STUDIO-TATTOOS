<script lang="ts">
/** Os tons disponíveis. Fica em bloco `<script>` comum, como em `AppSelect`,
 * porque `<script setup>` não exporta tipos para quem importa o componente — e
 * quem decide o tom de um estado de domínio precisa do mesmo conjunto, sob pena
 * de a união ser copiada e passar a divergir. */
export type BadgeTone = "neutral" | "positive" | "danger" | "warning" | "info";
</script>

<script setup lang="ts">
/** Selo de estado.
 *
 * O tom vem por mapa tipado. Os estados de agendamento e de orçamento são
 * entradas de dados na camada que os conhece — `QuoteDisplay`, por exemplo —,
 * e nada muda aqui dentro.
 *
 * O rótulo também vem de fora: `APPROVED` é o nome do estado na API, não o que
 * se escreve numa tela em inglês corrente. */
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
