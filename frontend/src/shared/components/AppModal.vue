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
/* `overflow-y: auto` e `align-items: start` no lugar de `center`: num celular
   deitado, ou num formulario longo, o modal centralizado passa das duas bordas
   da tela e o topo fica inalcancavel -- sem rolagem, o campo de cima some e
   nao ha como chegar ate ele. Isso e defeito, nao acabamento. */
.backdrop {
  position: fixed;
  z-index: var(--layer-modal);
  display: grid;
  place-items: start center;
  overflow-y: auto;
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
  margin-block: auto;
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
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
}

/* No celular o modal ocupa a largura toda, com respiro menor, e as acoes viram
   coluna: tres botoes lado a lado em 375px ficam estreitos demais para acertar
   com o polegar. */
@media (max-width: 40rem) {
  .backdrop {
    padding: var(--space-4);
  }

  .panel {
    gap: var(--space-4);
    padding: var(--space-5);
  }

  .actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }
}
</style>
