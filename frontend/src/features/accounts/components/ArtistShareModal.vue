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
 * **Os dois lados aparecem ao mesmo tempo, e isso não é enfeite.** O estúdio
 * enuncia os acordos pelo lado dele — "30% se o cliente foi trazido pelo
 * tatuador, 50% se foi indicação do estúdio, 15% em condições especiais" —, e o
 * sistema grava o do artista. Um campo pedindo só um número deixaria quem pensa
 * em 30 digitar 30, e o artista receberia 30% em vez de 70%. O complemento é
 * calculado enquanto se digita, para que o engano não chegue a ser salvo.
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

const studioKeeps = computed(() => display.studioShareOf(percentage.value));

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
        label="The artist keeps"
        type="number"
        placeholder="85"
        :disabled="props.busy"
      />

      <p
        v-if="!clearing"
        class="split"
      >
        <span>The studio keeps</span>
        <strong>{{ studioKeeps }}</strong>
      </p>

      <p class="hint">
        The studio's usual shares are <strong>30%</strong> on a client the artist
        brought (the artist keeps 70%), <strong>50%</strong> on a studio referral
        (50/50), and <strong>15%</strong> on special terms (the artist keeps
        85%).
      </p>

      <p class="hint">
        Leave it empty to end the agreement. The artist then follows the rule of
        where the client came from.
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

/* O outro lado da conta, calculado enquanto se digita: e o que impede digitar
   30 querendo dizer "a casa fica com 30". */
.split {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
}

.split span {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.split strong {
  font-size: var(--text-label-1);
  font-weight: var(--weight-medium);
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
