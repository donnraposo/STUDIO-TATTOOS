<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { AccountDisplay } from "@/features/accounts/AccountDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import type { StudioAccount } from "@/shared/domain/StudioAccount";

/** O acordo de percentual de um artista (ADR-030 e RN-CLI-003).
 *
 * O estúdio opera com mais de uma divisão — 85/15, 70/30 e 50/50 convivem no
 * mesmo mês, e o mesmo artista aparece em mais de uma. Aqui é onde a gestão
 * registra o que foi negociado com cada um.
 *
 * **Esvaziar o campo encerra o acordo** e devolve o artista à regra da origem.
 * É assim que um acordo termina, e não bloqueando a conta — por isso o campo
 * vazio é um envio válido, e não um erro de validação.
 *
 * **O aviso sobre trabalho já aprovado não é decorativo** (RN-REP-006). Sem
 * ele, o gestor que renegocia uma sexta-feira esperaria ver o repasse daquela
 * semana mudar, e abriria um chamado quando não mudasse. O percentual é
 * congelado na aprovação do orçamento; esta tela decide o que a próxima
 * aprovação vai congelar.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  account: StudioAccount;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ save: [percentage: string | null]; close: [] }>();

const display = new AccountDisplay();

const percentage = ref("");

watch(
  () => props.account,
  (account) => {
    percentage.value = account.defaultArtistPercentage ?? "";
  },
  { immediate: true },
);

const clearing = computed(() => percentage.value.trim() === "");

const action = computed(() => (clearing.value ? "End agreement" : "Save agreement"));

function save(): void {
  emit("save", clearing.value ? null : percentage.value.trim());
}
</script>

<template>
  <AppModal
    title="Artist share"
    @close="$emit('close')"
  >
    <div class="summary">
      <strong>{{ display.name(props.account) }}</strong>
      <span class="current">Currently {{ display.share(props.account) }}</span>
    </div>

    <form
      class="form"
      @submit.prevent="save"
    >
      <AppInput
        v-model="percentage"
        label="Share of each session"
        type="number"
        placeholder="85"
        :disabled="props.busy"
      />

      <p class="hint">
        Leave it empty to end the agreement. The artist then follows the origin
        rule — 70% on their own clients, 50% on studio referrals.
      </p>

      <p class="notice">
        This only applies to work approved from now on. Quotes already approved
        keep the share they were approved with.
      </p>

      <p
        v-if="props.failure"
        class="failure"
        role="alert"
      >
        {{ props.failure }}
      </p>
    </form>

    <template #actions>
      <AppButton
        tone="ghost"
        :disabled="props.busy"
        @click="$emit('close')"
      >
        Cancel
      </AppButton>
      <AppButton
        :busy="props.busy"
        @click="save"
      >
        {{ action }}
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.summary {
  display: flex;
  flex-direction: column;
}

.summary strong {
  font-weight: var(--weight-medium);
}

.current {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.hint {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

/* O aviso da RN-REP-006 em superfície própria: lido como parágrafo cinza ao
   lado da dica, passaria batido justamente por quem precisa dele. */
.notice {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-info-soft);
  color: var(--color-on-light);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
