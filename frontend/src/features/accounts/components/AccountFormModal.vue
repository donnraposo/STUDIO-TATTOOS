<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { AccountDisplay } from "@/features/accounts/AccountDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import AppCheckbox from "@/shared/components/AppCheckbox.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import { ArtistRole } from "@/shared/domain/ArtistRole";
import type { UserRole } from "@/shared/domain/AuthenticatedUser";
import type { StudioAccount } from "@/shared/domain/StudioAccount";

/** Cadastro de alguém da equipe: cria e edita (RN 2.1, 2.2 e 2.6).
 *
 * **O mesmo formulário serve aos dois casos** — `account` nulo cria, preenchido
 * edita —, pela mesma razão do cadastro de cliente: dois componentes quase
 * iguais divergiriam na primeira mudança de campo, e a diferença entre criar e
 * corrigir uma conta é um campo.
 *
 * **A senha só existe na criação.** Trocar senha encerra as sessões da conta
 * (RN 2.7) e é ato de outra natureza; no meio da edição, o gestor derrubaria
 * alguém ao corrigir um telefone.
 *
 * **Os papéis oferecidos chegam prontos**, pela alçada de quem opera: o gerente
 * cria residente e guest, o proprietário cria qualquer um. Na edição o seletor
 * é do proprietário — a RN 2.6 diz que o gerente não pode promover "nem alterar
 * perfis de acesso", e trocar residente por guest é alterar perfil: muda a
 * exigência de sinal e o repasse.
 *
 * **"Also tattoos" só aparece para gerente e proprietário.** Residente e guest
 * tatuam por definição, e oferecer-lhes a caixa sugeriria que existe residente
 * que não atende. O proprietário do estúdio atende, e é por isso que a caixa
 * existe: sem ela ele não apareceria na agenda nem no repasse.
 *
 * **O nome de artista é obrigatório de quem tatua**, e o banco recusa o
 * contrário. Exigi-lo aqui poupa o gestor de descobrir a regra por um 422
 * depois de preencher sete campos.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. O que
 * ele devolve é **tipo próprio** e não o corpo da requisição: um campo
 * renomeado no backend mudaria o contrato público dele, e quem traduz é a
 * tela. */
export interface AccountDraft {
  email: string;
  /** Nulo na edição: a senha não se troca por aqui. */
  password: string | null;
  fullName: string;
  phone: string;
  role: UserRole;
  actsAsArtist: boolean;
  artistName: string | null;
}

const props = defineProps<{
  account: StudioAccount | null;
  roles: UserRole[];
  canChangeRole: boolean;
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ submit: [account: AccountDraft]; close: [] }>();

/** O backend exige 12 caracteres. Repetido aqui para que o gestor saiba antes
 * de enviar, e não por um 422. */
const MINIMUM_PASSWORD = 12;

const display = new AccountDisplay();
const artists = new ArtistRole();

const fullName = ref("");
const artistName = ref("");
const email = ref("");
const phone = ref("");
const password = ref("");
const role = ref<UserRole>("RESIDENT");
const actsAsArtist = ref(false);

const isNew = computed(() => props.account === null);

const heading = computed(() =>
  props.account === null ? "New account" : `Edit ${display.name(props.account)}`,
);

watch(
  () => props.account,
  (account) => {
    fullName.value = account?.fullName ?? "";
    artistName.value = account?.artistName ?? "";
    email.value = account?.email ?? "";
    phone.value = account?.phone ?? "";
    password.value = "";
    role.value = account?.role ?? props.roles[0] ?? "RESIDENT";
    actsAsArtist.value = account?.actsAsArtist ?? false;
  },
  { immediate: true },
);

/** Na edição o papel atual entra na lista mesmo fora da alçada de quem edita:
 * sem ele o seletor abriria mostrando outro papel, e salvar mudaria o perfil de
 * alguém sem que ninguém tenha pedido. */
const roleOptions = computed<SelectOption[]>(() => {
  const offered = [...props.roles];
  if (props.account && !offered.includes(props.account.role)) {
    offered.unshift(props.account.role);
  }
  return offered.map((option) => ({ value: option, label: display.role(option) }));
});

/** Quem tatua por definição não precisa da caixa (RN 2.3). */
const asksAboutTattooing = computed(() => !artists.isAlways(role.value));

const tattoos = computed(() =>
  artists.includes(role.value, asksAboutTattooing.value ? actsAsArtist.value : false),
);

const roleLocked = computed(() => !isNew.value && !props.canChangeRole);

const passwordError = computed(() =>
  password.value !== "" && password.value.length < MINIMUM_PASSWORD
    ? `At least ${MINIMUM_PASSWORD} characters.`
    : null,
);

const ready = computed(
  () =>
    fullName.value.trim() !== "" &&
    email.value.trim() !== "" &&
    phone.value.trim() !== "" &&
    (!isNew.value || password.value.length >= MINIMUM_PASSWORD) &&
    (!tattoos.value || artistName.value.trim() !== ""),
);

function submit(): void {
  if (!ready.value) {
    return;
  }

  emit("submit", {
    email: email.value.trim(),
    password: isNew.value ? password.value : null,
    fullName: fullName.value.trim(),
    phone: phone.value.trim(),
    role: role.value,
    actsAsArtist: asksAboutTattooing.value && actsAsArtist.value,
    artistName: artistName.value.trim() === "" ? null : artistName.value.trim(),
  });
}
</script>

<template>
  <AppModal
    :title="heading"
    @close="$emit('close')"
  >
    <form
      class="form"
      @submit.prevent="submit"
    >
      <AppInput
        v-model="fullName"
        label="Full name"
        required
        :disabled="props.busy"
      />
      <AppInput
        v-model="artistName"
        label="Artist name"
        placeholder="How the studio calls them"
        :required="tattoos"
        :disabled="props.busy"
      />
      <AppInput
        v-model="email"
        label="Email"
        type="email"
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
      <AppSelect
        v-model="role"
        label="Role"
        :options="roleOptions"
        required
        :disabled="props.busy || roleLocked"
      />
      <p
        v-if="roleLocked"
        class="hint"
      >
        Only the owner can change the role of an account.
      </p>
      <AppCheckbox
        v-if="asksAboutTattooing"
        v-model="actsAsArtist"
        label="Also tattoos, with their own schedule and payouts"
        :disabled="props.busy"
      />
      <AppInput
        v-if="isNew"
        v-model="password"
        label="Temporary password"
        type="password"
        required
        autocomplete="new-password"
        :error="passwordError"
        :disabled="props.busy"
      />
      <p
        v-else
        class="hint"
      >
        The password is not changed here — changing it ends every session of the
        account.
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
        :disabled="!ready"
        :busy="props.busy"
        @click="submit"
      >
        {{ isNew ? "Create account" : "Save changes" }}
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.hint {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
