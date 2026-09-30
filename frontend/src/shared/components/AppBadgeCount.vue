<script setup lang="ts">
import { computed } from "vue";

/** Contador em pílula, para marcar quantidade ao lado de um rótulo.
 *
 * **Some quando é zero.** Um contador mostrando "0" ocupa o mesmo espaço e a
 * mesma atenção de um que mostra "3", e ensina o olho a ignorá-lo — que é
 * exatamente o oposto do que ele existe para fazer.
 *
 * Acima do limite mostra `9+`. O número exato deixa de importar muito antes
 * disso; o que importa é que há mais do que cabe na cabeça, e um contador de
 * três dígitos esticaria a pílula a ponto de empurrar o rótulo ao lado.
 *
 * Componente base: não conhece domínio. Quem sabe o que está sendo contado é
 * quem o usa. */
const props = withDefaults(defineProps<{ count: number; label?: string; max?: number }>(), {
  label: "",
  max: 9,
});

const visible = computed(() => props.count > 0);
const text = computed(() => (props.count > props.max ? `${props.max}+` : String(props.count)));
</script>

<template>
  <span
    v-if="visible"
    class="badge"
    :aria-label="props.label || undefined"
  >{{ text }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--badge-size);
  height: var(--badge-size);
  padding-inline: var(--space-2);
  border-radius: var(--radius-round);
  background: var(--gradient-gold);
  color: var(--color-ink);
  font-size: var(--text-kicker);
  font-weight: var(--weight-medium);
  line-height: var(--line-tight);
}
</style>
