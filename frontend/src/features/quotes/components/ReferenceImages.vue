<script setup lang="ts">
import AppButton from "@/shared/components/AppButton.vue";
import AppFileInput from "@/shared/components/AppFileInput.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import type { ReferenceImage } from "@/shared/domain/Quote";
import { ByteSize } from "@/shared/format/ByteSize";

/** Imagens de referência do orçamento (RN-ORC-004).
 *
 * Componente de apresentação: recebe a lista por `props` e devolve a intenção
 * por `emits`. Quem envia e quem apaga é a tela.
 *
 * **A miniatura aponta para `contentPath`, e não para um endereço assinado.** A
 * rota confere o cookie de sessão a cada leitura, então o navegador busca a
 * imagem como busca qualquer outra — e quem copiar o endereço sem sessão não vê
 * nada. É por isso que o caminho pode ficar à vista no HTML.
 *
 * **Anexar não devolve o orçamento a pendente.** A RN-ORC-003 trata de alterar
 * os termos do orçamento, e a foto do desenho não é um termo. */
const ACCEPTED_TYPES = "image/jpeg,image/png,image/webp";

const props = defineProps<{
  images: ReferenceImage[];
  canEdit: boolean;
  busy: boolean;
  failure: string | null;
}>();

defineEmits<{ attach: [file: File]; remove: [imageId: string] }>();

const size = new ByteSize();
</script>

<template>
  <section class="images">
    <header>
      <SectionKicker label="Reference images" />
      <AppFileInput
        v-if="props.canEdit"
        label="Add image"
        :accept="ACCEPTED_TYPES"
        :disabled="props.busy"
        @select="$emit('attach', $event)"
      />
    </header>

    <p
      v-if="props.images.length === 0"
      class="none"
    >
      No reference images yet.
    </p>

    <ul v-else>
      <li
        v-for="image in props.images"
        :key="image.id"
      >
        <img
          :src="image.contentPath"
          alt="Reference"
        >
        <span class="size">{{ size.human(image.byteSize) }}</span>
        <AppButton
          v-if="props.canEdit"
          tone="ghost"
          :disabled="props.busy"
          @click="$emit('remove', image.id)"
        >
          Remove
        </AppButton>
      </li>
    </ul>

    <p
      v-if="props.failure"
      class="failure"
      role="alert"
    >
      {{ props.failure }}
    </p>
  </section>
</template>

<style scoped>
.images {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.none {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

ul {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--thumb-size), 1fr));
  gap: var(--space-3);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

li {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

img {
  width: 100%;
  height: var(--thumb-size);
  border-radius: var(--radius-sm);
  background: var(--color-surface-soft);
  object-fit: cover;
}

.size {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
