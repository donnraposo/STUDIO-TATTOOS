<script setup lang="ts">
/** Superfície elevada.
 *
 * Cabeçalho e rodapé entram por `slot` e não por `prop` booleana: o que varia é
 * conteúdo, e três booleanos ligando pedaços de marcação seriam três
 * componentes esperando para nascer. */
withDefaults(defineProps<{ title?: string }>(), { title: "" });
</script>

<template>
  <section class="card">
    <header
      v-if="title || $slots.header"
      class="card-header"
    >
      <h3 v-if="title">
        {{ title }}
      </h3>
      <slot name="header" />
    </header>
    <div class="card-body">
      <slot />
    </div>
    <footer
      v-if="$slots.footer"
      class="card-footer"
    >
      <slot name="footer" />
    </footer>
  </section>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: var(--border-thin);
}
</style>
