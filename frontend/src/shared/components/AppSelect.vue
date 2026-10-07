<script lang="ts">
/** Uma opção do seletor. Fica em bloco `<script>` comum porque `<script setup>`
 * não exporta tipos para quem importa o componente. */
export interface SelectOption {
  value: string;
  label: string;
}
</script>

<script setup lang="ts">
import AppField from "@/shared/components/AppField.vue";

/** Seleção de uma opção entre poucas.
 *
 * Honra o mesmo contrato do `AppInput`, e divide com ele a moldura do
 * `AppField` e a pílula da classe `control` — o seletor e o campo de texto
 * precisam ser indistinguíveis em altura e tratamento.
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
</script>

<template>
  <AppField
    :label="props.label"
    :error="props.error"
    :required="props.required"
  >
    <template #default="{ fieldId, describedBy }">
      <select
        :id="fieldId"
        class="control"
        :value="props.modelValue"
        :disabled="props.disabled"
        :required="props.required"
        :aria-invalid="Boolean(props.error)"
        :aria-describedby="describedBy"
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
    </template>
  </AppField>
</template>
