<script setup lang="ts">
import { ref } from "vue";

import AppButton from "@/shared/components/AppButton.vue";

/** Escolha de um arquivo.
 *
 * O `<input type="file">` nativo desenha um botão próprio, que nenhum navegador
 * deixa estilizar por completo — ele ficaria com outra altura, outra fonte e
 * outro canto, ao lado de botões que o projeto alinhou com cuidado. Por isso o
 * controle real fica escondido e quem aparece é o `AppButton`.
 *
 * Escondido com `position: absolute` e `opacity`, e **não** com `display: none`:
 * um campo removido do fluxo dessa forma deixa de ser alcançável pelo teclado,
 * e a escolha de arquivo passaria a exigir o mouse.
 *
 * O valor é limpo depois de cada escolha. Sem isso, escolher o mesmo arquivo
 * duas vezes seguidas não dispara evento nenhum — o navegador entende que nada
 * mudou —, e quem acabou de corrigir a imagem no disco conclui que o sistema
 * travou. */
const props = withDefaults(
  defineProps<{ label: string; accept?: string; disabled?: boolean }>(),
  { accept: "", disabled: false },
);

const emit = defineEmits<{ select: [file: File] }>();

const field = ref<HTMLInputElement | null>(null);

function choose(): void {
  field.value?.click();
}

function onChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) {
    emit("select", file);
  }
  input.value = "";
}
</script>

<template>
  <div class="picker">
    <AppButton
      tone="ghost"
      :disabled="props.disabled"
      @click="choose"
    >
      {{ props.label }}
    </AppButton>

    <input
      ref="field"
      class="hidden"
      type="file"
      :accept="props.accept"
      :disabled="props.disabled"
      :aria-label="props.label"
      @change="onChange"
    >
  </div>
</template>

<style scoped>
.picker {
  display: inline-flex;
  position: relative;
}

.hidden {
  position: absolute;
  width: var(--space-1);
  height: var(--space-1);
  opacity: var(--opacity-invisible);
  inset: var(--space-0);
}
</style>
