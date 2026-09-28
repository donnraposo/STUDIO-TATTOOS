<script setup lang="ts">
import type { ClientContact } from "@/shared/domain/Client";
import AppButton from "@/shared/components/AppButton.vue";

/** Aviso de possível duplicidade (RN-CLI-005).
 *
 * **Avisa, não bloqueia, e o texto precisa deixar isso claro.** O cliente já
 * foi cadastrado quando este aviso aparece — duas pessoas podem legitimamente
 * dividir um telefone, e travar o cadastro atrapalharia o atendimento. Se a
 * mensagem soar como erro, quem estiver na recepção vai achar que precisa
 * refazer alguma coisa.
 *
 * Tom de atenção, não de perigo: nada deu errado. */
defineProps<{ duplicates: ClientContact[] }>();

defineEmits<{ dismiss: [] }>();
</script>

<template>
  <aside class="warning">
    <div class="text">
      <strong>Saved. Possible duplicate.</strong>
      <p>
        These clients share the phone or Instagram you entered. The new client was created
        anyway — merge them later if they are the same person.
      </p>
      <ul>
        <li
          v-for="duplicate in duplicates"
          :key="duplicate.id"
        >
          {{ duplicate.name }} · {{ duplicate.phone }}
        </li>
      </ul>
    </div>

    <AppButton
      tone="ghost"
      @click="$emit('dismiss')"
    >
      Got it
    </AppButton>
  </aside>
</template>

<style scoped>
.warning {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.text {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

p {
  max-width: var(--content-measure);
  font-size: var(--text-label-3);
}

ul {
  margin: var(--space-0);
  padding-left: var(--space-5);
  font-size: var(--text-label-3);
}
</style>
