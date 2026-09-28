<script setup lang="ts">
/** Espera. `role="status"` para que leitores de tela anunciem, em vez de a
 * mudança passar em silêncio. */
withDefaults(defineProps<{ message?: string }>(), { message: "Loading…" });
</script>

<template>
  <div
    class="state"
    role="status"
  >
    <span
      class="spinner"
      aria-hidden="true"
    />
    <p>{{ message }}</p>
  </div>
</template>

<style scoped>
.state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-10);
  color: var(--color-muted);
}

.spinner {
  width: var(--icon-size);
  height: var(--icon-size);
  border: var(--border-thin);
  border-top-color: var(--color-gold);
  border-radius: var(--radius-round);
  animation: spin var(--transition-slow) linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(1turn);
  }
}
</style>
