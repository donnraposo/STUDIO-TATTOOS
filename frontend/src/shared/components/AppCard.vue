<script setup lang="ts">
/** Superfície elevada.
 *
 * Cabeçalho e rodapé entram por `slot` e não por `prop` booleana: o que varia é
 * conteúdo, e três booleanos ligando pedaços de marcação seriam três
 * componentes esperando para nascer.
 *
 * **O cartão ocupa a célula inteira e o rodapé encosta embaixo.** Numa grade,
 * cartões com conteúdo de tamanhos diferentes terminavam em alturas diferentes,
 * e as ações de cada um flutuavam numa linha própria — a lista parecia
 * desalinhada porque estava. Com a altura cheia e o corpo crescendo, os botões
 * de todos os cartões de uma linha ficam na mesma altura.
 *
 * **O rodapé quebra linha.** Sem isso, três ações não cabiam na largura do
 * cartão e **transbordavam para fora dele** — os botões apareciam por cima do
 * cartão vizinho. É o tipo de defeito que só aparece quando alguém ganha a
 * terceira ação, meses depois de o componente ter sido escrito. */
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
  height: 100%;
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

/* O corpo cresce para empurrar o rodape ate embaixo; sem isso as acoes param
   onde o conteudo acabou, e cada cartao da linha para num lugar. */
.card-body {
  flex: 1;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.card-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: var(--border-thin);
}
</style>
