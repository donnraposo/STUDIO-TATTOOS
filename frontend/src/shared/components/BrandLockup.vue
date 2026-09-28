<script setup lang="ts">
/** Monograma e nome do estúdio, juntos.
 *
 * Existe porque o conjunto aparecia em dois lugares — menu lateral e login — e
 * o estilo estava escrito duas vezes. Duplicado, ele já tinha começado a
 * divergir: bastava um dos dois manter a máscara redonda antiga para a marca
 * aparecer cortada em metade do sistema.
 *
 * O monograma entra como fundo, não como `<img>`. É decorativo, porque o nome
 * está escrito ao lado, e assim o Vite não tenta transformar o arquivo em
 * módulo — que era o que devolvia JavaScript no lugar da imagem.
 *
 * **A proporção é retrato.** `contain` com `aspect-ratio` mostra o escudo
 * inteiro; caixa quadrada com `cover` o corta em cima e embaixo. */
type LockupSize = "compact" | "large";

const SIZE_CLASS: Record<LockupSize, string> = {
  compact: "is-compact",
  large: "is-large",
};

withDefaults(defineProps<{ name: string; size?: LockupSize }>(), { size: "compact" });
</script>

<template>
  <div class="lockup">
    <span
      class="mark"
      :class="SIZE_CLASS[size]"
      aria-hidden="true"
    />
    <span class="name">{{ name }}</span>
  </div>
</template>

<style scoped>
.lockup {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.mark {
  display: block;
  flex-shrink: 0;
  aspect-ratio: var(--brand-mark-ratio);
  background-image: var(--image-logo);
  background-position: center;
  background-size: contain;
  background-repeat: no-repeat;
}

.is-compact {
  height: var(--icon-box);
}

.is-large {
  height: var(--brand-mark-size);
}

.name {
  font-weight: var(--weight-medium);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}
</style>
