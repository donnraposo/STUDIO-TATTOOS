<script setup lang="ts">
/** Ausência de dado, que não é erro.
 *
 * Existe para que nenhuma tela desenhe o seu próprio "nada encontrado" — cada
 * uma escrevendo uma frase diferente para a mesma situação é como uma interface
 * começa a parecer feita por quatro pessoas. */
withDefaults(defineProps<{ title: string; description?: string }>(), { description: "" });
</script>

<template>
  <div class="state">
    <h3>{{ title }}</h3>
    <p v-if="description">
      {{ description }}
    </p>
    <slot name="action" />
  </div>
</template>

<style scoped>
.state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  max-width: var(--content-measure);
  margin-inline: auto;
  padding: var(--space-10);
  text-align: center;
  color: var(--color-muted);
}
</style>
