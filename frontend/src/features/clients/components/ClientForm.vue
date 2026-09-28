<script setup lang="ts">
import { ref, watch } from "vue";

import type { Client } from "@/shared/domain/Client";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import AppInput from "@/shared/components/AppInput.vue";

/** Cadastro e edição de cliente (RN-CLI-001).
 *
 * Nome e telefone obrigatórios, Instagram opcional. O mesmo formulário serve
 * aos dois casos: `client` nulo cria, preenchido edita. Dois componentes quase
 * iguais divergiriam na primeira mudança de campo.
 *
 * O estado dos campos é interno e copiado de `client` — não escreve na entidade
 * recebida. Editar o objeto do pai faria a lista mudar enquanto se digita, e
 * cancelar não teria como desfazer. */
const props = defineProps<{ client: Client | null; busy: boolean; failure: string | null }>();

const emit = defineEmits<{
  submit: [values: { name: string; phone: string; instagram: string | null }];
  cancel: [];
}>();

const name = ref("");
const phone = ref("");
const instagram = ref("");

watch(
  () => props.client,
  (client) => {
    name.value = client?.name ?? "";
    phone.value = client?.phone ?? "";
    instagram.value = client?.instagram ?? "";
  },
  { immediate: true },
);

function submit(): void {
  emit("submit", {
    name: name.value,
    phone: phone.value,
    instagram: instagram.value.trim() === "" ? null : instagram.value,
  });
}
</script>

<template>
  <AppCard :title="props.client ? 'Edit client' : 'New client'">
    <form
      class="form"
      @submit.prevent="submit"
    >
      <AppInput
        v-model="name"
        label="Name"
        required
        :disabled="props.busy"
      />
      <AppInput
        v-model="phone"
        label="Phone"
        type="tel"
        required
        :disabled="props.busy"
      />
      <AppInput
        v-model="instagram"
        label="Instagram"
        placeholder="@handle"
        :disabled="props.busy"
      />

      <p
        v-if="props.failure"
        class="failure"
        role="alert"
      >
        {{ props.failure }}
      </p>

      <div class="actions">
        <AppButton
          tone="ghost"
          :disabled="props.busy"
          @click="$emit('cancel')"
        >
          Cancel
        </AppButton>
        <AppButton
          type="submit"
          :busy="props.busy"
        >
          {{ props.client ? "Save changes" : "Create client" }}
        </AppButton>
      </div>
    </form>
  </AppCard>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>
