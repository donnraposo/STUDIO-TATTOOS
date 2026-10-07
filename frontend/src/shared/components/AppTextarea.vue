<script setup lang="ts">
import AppField from "@/shared/components/AppField.vue";

/** Campo de texto longo.
 *
 * Honra o mesmo contrato do `AppInput` — `modelValue`, `update:modelValue`,
 * `disabled` e `error` — e divide com ele a moldura do `AppField` e a pílula da
 * classe `control`.
 *
 * Existe porque a descrição da tatuagem e as observações do orçamento
 * (RN-ORC-004) são texto de vários parágrafos, e escrevê-los numa linha única
 * esconde do autor o que ele acabou de digitar. Sem este componente, a tela
 * usaria um `<textarea>` cru — e aí o campo sairia do padrão de altura, cor e
 * foco na primeira tela que o usasse.
 *
 * O raio arredondado da pílula é o único ponto em que este campo se afasta do
 * `control`: numa caixa de várias linhas ele arredondaria as pontas do texto
 * para dentro. */
const props = withDefaults(
  defineProps<{
    modelValue: string;
    label: string;
    rows?: number;
    placeholder?: string;
    error?: string | null;
    disabled?: boolean;
    required?: boolean;
  }>(),
  { rows: 4, placeholder: "", error: null, disabled: false, required: false },
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
      <textarea
        :id="fieldId"
        class="control"
        :value="props.modelValue"
        :rows="props.rows"
        :placeholder="props.placeholder"
        :disabled="props.disabled"
        :required="props.required"
        :aria-invalid="Boolean(props.error)"
        :aria-describedby="describedBy"
        @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      />
    </template>
  </AppField>
</template>

<style scoped>
.control {
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-md);
  resize: vertical;
}
</style>
