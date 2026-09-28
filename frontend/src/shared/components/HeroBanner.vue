<script setup lang="ts">
import SectionKicker from "@/shared/components/SectionKicker.vue";

/** Cartão herói: banner escuro, título grande e uma ação clara.
 *
 * O fundo é o banner em SVG e entra como imagem de CSS, não como `<img>`: é
 * decoração, e um leitor de tela não ganha nada anunciando-a. O texto é
 * marcação por cima, para poder mudar sem gerar imagem nova.
 *
 * Uma ação só, por `slot`. Dois botões de igual peso num herói é a forma mais
 * rápida de a tela não dizer nada: se tudo é principal, nada é. */
defineProps<{ kicker: string; title: string; description?: string }>();
</script>

<template>
  <section class="hero">
    <div class="content">
      <SectionKicker
        :label="kicker"
        on-dark
      />
      <h2>{{ title }}</h2>
      <p v-if="description">
        {{ description }}
      </p>
      <div
        v-if="$slots.action"
        class="action"
      >
        <slot name="action" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  display: flex;
  align-items: flex-end;
  min-height: var(--hero-height);
  padding: var(--space-10);
  border-radius: var(--radius-xl);
  background-color: var(--color-black);
  background-image: url("/brand/banner.svg");
  background-position: center right;
  background-size: cover;
  color: var(--color-on-dark);
}

.content {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  max-width: var(--content-measure);
}

h2 {
  font-size: var(--text-display-2);
  letter-spacing: var(--tracking-display);
  line-height: var(--line-display);
}

p {
  color: var(--color-on-dark-muted);
}

.action {
  margin-top: var(--space-4);
}

@media (max-width: 40rem) {
  .hero {
    padding: var(--space-6);
  }
}
</style>
