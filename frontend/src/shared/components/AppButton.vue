<script setup lang="ts">
/** Botão base. A variação de aparência entra por mapa tipado, não por cadeia de
 * `v-if`: acrescentar um tom passa a ser uma linha de dados. */
type ButtonTone = "primary" | "ghost" | "light" | "danger";

const TONE_CLASS: Record<ButtonTone, string> = {
  primary: "is-primary",
  ghost: "is-ghost",
  light: "is-light",
  danger: "is-danger",
};

const props = withDefaults(
  defineProps<{
    tone?: ButtonTone;
    type?: "button" | "submit";
    disabled?: boolean;
    busy?: boolean;
    block?: boolean;
  }>(),
  { tone: "primary", type: "button", disabled: false, busy: false, block: false },
);

defineEmits<{ click: [event: MouseEvent] }>();
</script>

<template>
  <button
    :type="props.type"
    :class="[TONE_CLASS[props.tone], { 'is-block': props.block }]"
    :disabled="props.disabled || props.busy"
    :aria-busy="props.busy"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<style scoped>
button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  border: none;
  border-radius: var(--radius-round);
  font-size: var(--text-label-2);
  font-weight: var(--weight-medium);
}

button:disabled {
  cursor: not-allowed;
  opacity: var(--opacity-disabled);
}

.is-block {
  width: 100%;
}

.is-primary {
  background: var(--gradient-gold);
  color: var(--color-ink);
}

.is-primary:hover:not(:disabled) {
  box-shadow: var(--shadow-gold);
}

.is-ghost {
  border: var(--border-thin);
  background: transparent;
  color: var(--color-on-light);
}

.is-ghost:hover:not(:disabled) {
  background: var(--color-surface-soft);
}

/* Para uso sobre superfície escura, como o cartão herói: ali o gradiente ouro
   perderia o contraste contra o próprio fundo dourado do banner. */
.is-light {
  background: var(--color-surface);
  color: var(--color-ink);
}

.is-light:hover:not(:disabled) {
  box-shadow: var(--shadow-raised);
}

.is-danger {
  background: var(--color-danger);
  color: var(--color-surface);
}

.is-danger:hover:not(:disabled) {
  box-shadow: var(--shadow-raised);
}
</style>
