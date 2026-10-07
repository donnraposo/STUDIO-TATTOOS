<script setup lang="ts">
import SectionKicker from "@/shared/components/SectionKicker.vue";

/** Abertura de toda tela: rótulo, título de display e ações à direita.
 *
 * Existe para que nenhuma tela decida sozinha o tamanho do próprio título. A
 * referência sustenta a página num título grande com muito silêncio em volta, e
 * é isso que se perde primeiro quando cada tela improvisa o seu.
 *
 * As ações entram por `slot`: o cabeçalho não sabe nem precisa saber se o que
 * vem ali é um botão, dois, ou nenhum. */
defineProps<{ kicker: string; title: string }>();
</script>

<template>
  <header class="page-header">
    <div class="titles">
      <SectionKicker :label="kicker" />
      <h1>{{ title }}</h1>
    </div>
    <div
      v-if="$slots.actions"
      class="actions"
    >
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-6);
  padding-bottom: var(--space-6);
  border-bottom: var(--border-thin);
}

.titles {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

h1 {
  font-size: var(--text-display-2);
  letter-spacing: var(--tracking-display);
  line-height: var(--line-display);
}

/* `flex-end` e nao o `stretch` padrao: quando uma das acoes e um campo com
   rotulo em cima, o botao ao lado esticaria para acompanhar a pilha inteira e
   apareceria muito mais alto que o campo. Alinhados pela base, os dois
   terminam na mesma linha. */
.actions {
  display: flex;
  flex-shrink: 0;
  align-items: flex-end;
  gap: var(--space-3);
}

@media (max-width: 40rem) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-4);
  }

  /* As acoes dividem a largura em vez de se espremerem num canto: num telefone,
     um campo de data e um botao lado a lado deixam os dois pequenos demais. */
  .actions {
    flex-wrap: wrap;
  }

  .actions > * {
    flex: 1 1 100%;
  }
}
</style>
