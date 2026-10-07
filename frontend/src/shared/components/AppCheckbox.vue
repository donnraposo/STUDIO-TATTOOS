<script setup lang="ts">
/** Caixa de marcação.
 *
 * Honra o mesmo contrato dos demais campos — `modelValue`,
 * `update:modelValue`, `disabled` — trocando texto por booleano.
 *
 * Existe pelo mesmo motivo dos outros: sem ele, cada formulário escreve o seu
 * `<input type="checkbox">` com o próprio espaçamento e o próprio tamanho de
 * rótulo, e a interface deixa de parecer feita pela mesma pessoa. */
const props = withDefaults(
  defineProps<{ modelValue: boolean; label: string; disabled?: boolean }>(),
  { disabled: false },
);

defineEmits<{ "update:modelValue": [value: boolean] }>();
</script>

<template>
  <label
    class="checkbox"
    :class="{ 'is-disabled': props.disabled }"
  >
    <input
      type="checkbox"
      :checked="props.modelValue"
      :disabled="props.disabled"
      @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    >
    <span>{{ props.label }}</span>
  </label>
</template>

<style scoped>
.checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: var(--touch-target);
  color: var(--color-on-light);
  font-size: var(--text-label-3);
  cursor: pointer;
}

.is-disabled {
  cursor: not-allowed;
  opacity: var(--opacity-disabled);
}

input {
  width: var(--icon-size);
  height: var(--icon-size);
  accent-color: var(--color-gold);
  cursor: inherit;
}
</style>
