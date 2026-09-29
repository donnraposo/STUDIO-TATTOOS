<script setup lang="ts">
import { onBeforeUnmount, onMounted } from "vue";

/** Sobreposição com decisão.
 *
 * `dismissible` existe porque nem toda sobreposição pode ser fechada no
 * impulso. O modal de conflito da RN-AGE-007 **não** oferece saída pelo fundo
 * nem pela tecla Esc: fechar sem ler é, na prática, ignorar o conflito — que é
 * exatamente o que a regra proíbe. Um formulário, ao contrário, precisa poder
 * ser abandonado.
 *
 * O `Escape` é escutado no documento e não no elemento porque o foco pode estar
 * em qualquer campo dentro do modal. */
const props = withDefaults(
  defineProps<{ title: string; dismissible?: boolean }>(),
  { dismissible: true },
);

const emit = defineEmits<{ close: [] }>();

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape" && props.dismissible) {
    emit("close");
  }
}

onMounted(() => document.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => document.removeEventListener("keydown", onKeydown));
</script>

<template>
  <div
    class="backdrop"
    @click.self="props.dismissible && emit('close')"
  >
    <section
      class="panel"
      role="dialog"
      aria-modal="true"
      :aria-label="props.title"
    >
      <h2>{{ props.title }}</h2>
      <div class="body">
        <slot />
      </div>
      <footer class="actions">
        <slot name="actions" />
      </footer>
    </section>
  </div>
</template>

<style scoped>
.backdrop {
  position: fixed;
  z-index: var(--layer-modal);
  display: grid;
  place-items: center;
  padding: var(--space-page);
  inset: var(--space-0);
  background: var(--overlay-backdrop);
}

.panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  width: 100%;
  max-width: var(--content-measure);
  padding: var(--space-8);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-raised);
}

h2 {
  font-size: var(--text-heading-2);
  letter-spacing: var(--tracking-display);
}

.body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>
