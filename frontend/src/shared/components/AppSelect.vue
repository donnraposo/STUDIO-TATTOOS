<script lang="ts">
/** Uma opção do seletor. Fica em bloco `<script>` comum porque `<script setup>`
 * não exporta tipos para quem importa o componente. */
export interface SelectOption {
  value: string;
  label: string;
}
</script>

<script setup lang="ts">
/** Seleção de uma opção entre poucas.
 *
 * Honra o mesmo contrato do `AppInput` — `modelValue`, `update:modelValue`,
 * `disabled`, `error` — para que um formulário troque um campo por outro sem
 * saber qual é.
 *
 * As opções entram como dados, e não como `slot` de `<option>`: assim o
 * componente controla a marcação e nenhuma tela reinventa o estado vazio. */
const props = withDefaults(
  defineProps<{
    modelValue: string;
    label: string;
    options: SelectOption[];
    placeholder?: string;
    error?: string | null;
    disabled?: boolean;
    required?: boolean;
  }>(),
  { placeholder: "", error: null, disabled: false, required: false },
);

defineEmits<{ "update:modelValue": [value: string] }>();

const fieldId = `select-${Math.random().toString(36).slice(2)}`;
const errorId = `${fieldId}-error`;
</script>

<template>
  <div class="field">
    <label :for="fieldId">
      {{ props.label }}
      <span
        v-if="props.required"
        aria-hidden="true"
      >*</span>
    </label>
    <select
      :id="fieldId"
      :value="props.modelValue"
      :disabled="props.disabled"
      :required="props.required"
      :aria-invalid="Boolean(props.error)"
      :aria-describedby="props.error ? errorId : undefined"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option
        v-if="props.placeholder"
        value=""
        disabled
      >
        {{ props.placeholder }}
      </option>
      <option
        v-for="option in props.options"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>
    <p
      v-if="props.error"
      :id="errorId"
      class="error"
      role="alert"
    >
      {{ props.error }}
    </p>
  </div>
</template>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

label {
  color: var(--color-muted);
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
}

select {
  min-height: var(--touch-target);
  padding: var(--space-2) var(--space-5);
  border: var(--border-thin);
  border-color: transparent;
  border-radius: var(--radius-round);
  background: var(--color-field);
  color: var(--color-on-light);
}

select:hover:not(:disabled) {
  border-color: var(--color-border);
}

select:disabled {
  background: var(--color-surface-soft);
  opacity: var(--opacity-disabled);
}

select[aria-invalid="true"] {
  border-color: var(--color-danger);
}

.error {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
