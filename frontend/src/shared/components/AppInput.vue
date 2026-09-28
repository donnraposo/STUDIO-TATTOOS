<script setup lang="ts">
/** Campo de texto base.
 *
 * Honra o contrato que todo campo do projeto honra — `modelValue`,
 * `update:modelValue`, `disabled` e `error` — para que um formulário possa
 * trocar um campo por outro sem saber qual é. */
const props = withDefaults(
  defineProps<{
    modelValue: string;
    label: string;
    type?: "text" | "email" | "password" | "tel" | "number" | "date";
    placeholder?: string;
    error?: string | null;
    disabled?: boolean;
    required?: boolean;
    autocomplete?: string;
  }>(),
  {
    type: "text",
    placeholder: "",
    error: null,
    disabled: false,
    required: false,
    autocomplete: "off",
  },
);

defineEmits<{ "update:modelValue": [value: string] }>();

const fieldId = `field-${Math.random().toString(36).slice(2)}`;
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
    <input
      :id="fieldId"
      :value="props.modelValue"
      :type="props.type"
      :placeholder="props.placeholder"
      :disabled="props.disabled"
      :required="props.required"
      :autocomplete="props.autocomplete"
      :aria-invalid="Boolean(props.error)"
      :aria-describedby="props.error ? errorId : undefined"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    >
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

/* Pílula com preenchimento sutil, como na referência: o campo se lê como área
   clicável sem competir com o botão, que é quem deve puxar o olho. */
input {
  min-height: var(--touch-target);
  padding: var(--space-2) var(--space-5);
  border: var(--border-thin);
  border-color: transparent;
  border-radius: var(--radius-round);
  background: var(--color-field);
  color: var(--color-on-light);
}

input:hover:not(:disabled) {
  border-color: var(--color-border);
}

input:disabled {
  background: var(--color-surface-soft);
  opacity: var(--opacity-disabled);
}

input[aria-invalid="true"] {
  border-color: var(--color-danger);
}

.error {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
