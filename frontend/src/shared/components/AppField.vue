<script setup lang="ts">
/** A moldura de um campo: rótulo, marca de obrigatório e mensagem de erro.
 *
 * Existe porque `AppInput` e `AppSelect` escreviam exatamente o mesmo rótulo,
 * a mesma marca e a mesma mensagem — três blocos idênticos que já começariam a
 * divergir no primeiro ajuste de espaçamento.
 *
 * O controle em si entra por `slot`, recebendo o `id` e o `aria-describedby`
 * que esta moldura gera. É o que permite trocar `<input>` por `<select>` sem
 * que a moldura saiba qual dos dois está lá dentro. */
const props = withDefaults(
  defineProps<{ label: string; error?: string | null; required?: boolean }>(),
  { error: null, required: false },
);

const fieldId = `field-${Math.random().toString(36).slice(2)}`;
const errorId = `${fieldId}-error`;

defineExpose({ fieldId, errorId });
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

    <slot
      :field-id="fieldId"
      :described-by="props.error ? errorId : undefined"
    />

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

.error {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
