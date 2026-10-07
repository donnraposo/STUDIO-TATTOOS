<script setup lang="ts">
import AppField from "@/shared/components/AppField.vue";

/** Campo de texto base.
 *
 * Honra o contrato que todo campo do projeto honra — `modelValue`,
 * `update:modelValue`, `disabled` e `error` — para que um formulário possa
 * trocar um campo por outro sem saber qual é.
 *
 * O rótulo, a marca de obrigatório e a mensagem de erro vêm do `AppField`, e a
 * aparência da pílula vem da classe `control` em `base.css`. Este arquivo cuida
 * só do que é específico de um `<input>`. */
const props = withDefaults(
  defineProps<{
    modelValue: string;
    label: string;
    type?: "text" | "email" | "password" | "tel" | "number" | "date" | "time";
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
</script>

<template>
  <AppField
    :label="props.label"
    :error="props.error"
    :required="props.required"
  >
    <template #default="{ fieldId, describedBy }">
      <input
        :id="fieldId"
        class="control"
        :value="props.modelValue"
        :type="props.type"
        :placeholder="props.placeholder"
        :disabled="props.disabled"
        :required="props.required"
        :autocomplete="props.autocomplete"
        :aria-invalid="Boolean(props.error)"
        :aria-describedby="describedBy"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      >
    </template>
  </AppField>
</template>
