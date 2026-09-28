<script setup lang="ts">
/** Rótulo em caixa alta acima de um título.
 *
 * Na referência de design ele aparece sobre **todo** título, e é o que dá ritmo
 * à página: diz onde você está antes de dizer o que há ali. Sem ele, cada tela
 * começa com um título solto e todas se parecem.
 *
 * `on-dark` porque o mesmo rótulo aparece sobre o off-white e sobre a foto do
 * herói, e ouro sobre branco não tem contraste suficiente para um texto tão
 * pequeno. */
withDefaults(defineProps<{ label: string; onDark?: boolean }>(), { onDark: false });
</script>

<template>
  <p
    class="kicker"
    :class="{ 'on-dark': onDark }"
  >
    {{ label }}
  </p>
</template>

<style scoped>
.kicker {
  color: var(--color-muted);
  font-size: var(--text-kicker);
  font-weight: var(--weight-medium);
  letter-spacing: var(--tracking-kicker);
  text-transform: uppercase;
}

.on-dark {
  color: var(--color-gold);
}
</style>
