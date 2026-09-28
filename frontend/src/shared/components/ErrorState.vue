<script setup lang="ts">
import AppButton from "@/shared/components/AppButton.vue";

/** Falha recuperável.
 *
 * A mensagem vem do backend, que já escreve em inglês e voltada ao usuário
 * (ADR-021). Reescrevê-la aqui criaria duas versões da mesma explicação.
 *
 * `retry` é opcional porque nem toda falha se resolve tentando de novo: um 403
 * não muda por insistência, e oferecer o botão ali seria enganar. */
withDefaults(defineProps<{ message: string; retryable?: boolean }>(), { retryable: true });

defineEmits<{ retry: [] }>();
</script>

<template>
  <div
    class="state"
    role="alert"
  >
    <p>{{ message }}</p>
    <AppButton
      v-if="retryable"
      tone="ghost"
      @click="$emit('retry')"
    >
      Try again
    </AppButton>
  </div>
</template>

<style scoped>
.state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  max-width: var(--content-measure);
  margin-inline: auto;
  padding: var(--space-8);
  border: var(--border-thin);
  border-color: var(--color-danger);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  text-align: center;
}
</style>
