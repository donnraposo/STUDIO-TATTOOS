<script setup lang="ts">
import { computed, ref } from "vue";

import { AccountDisplay } from "@/features/accounts/AccountDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import AppCheckbox from "@/shared/components/AppCheckbox.vue";
import AppInput from "@/shared/components/AppInput.vue";
import AppModal from "@/shared/components/AppModal.vue";
import AppSelect, { type SelectOption } from "@/shared/components/AppSelect.vue";
import { ArtistRole } from "@/shared/domain/ArtistRole";
import type { UserRole } from "@/shared/domain/AuthenticatedUser";

/** Conta nova para alguém da equipe (RN 2.1 e 2.2).
 *
 * **Os papéis oferecidos chegam prontos**, pela alçada de quem está criando: o
 * gerente cria residente e guest, o proprietário cria qualquer um. Filtrar aqui
 * faria este componente conhecer a matriz de permissões, que já tem um lugar.
 *
 * **"Also tattoos" só aparece para gerente e proprietário.** Residente e guest
 * tatuam por definição, e oferecer-lhes a caixa sugeriria que existe residente
 * que não atende. O proprietário do estúdio atende, e é por isso que a caixa
 * existe: sem ela ele não apareceria na agenda nem no repasse.
 *
 * **O nome de artista é obrigatório de quem tatua**, e o banco recusa o
 * contrário (`ck_user_account_artist_name_required`). Exigi-lo aqui poupa o
 * gestor de descobrir a regra por um 422 depois de preencher sete campos. Para
 * um gerente que não atende ele é opcional e, quando vazio, desce nulo: texto
 * vazio gravaria um nome de artista em branco, que é diferente de não ter.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. O que
 * ele devolve é **tipo próprio** e não o corpo da requisição: um campo
 * renomeado no backend mudaria o contrato público deste componente, e quem
 * traduz é a tela. */
export interface AccountDraft {
  email: string;
  password: string;
  fullName: string;
  phone: string;
  role: UserRole;
  actsAsArtist: boolean;
  artistName: string | null;
}

const props = defineProps<{
  roles: UserRole[];
  busy: boolean;
  failure: string | null;
}>();

const emit = defineEmits<{ submit: [account: AccountDraft]; close: [] }>();

/** O backend exige 12 caracteres (`CreateAccountRequest`). Repetido aqui para
 * que o gestor saiba antes de enviar, e não por um 422. */
const MINIMUM_PASSWORD = 12;

const display = new AccountDisplay();
const artists = new ArtistRole();

const fullName = ref("");
const artistName = ref("");
const email = ref("");
const phone = ref("");
const password = ref("");
const role = ref<UserRole>(props.roles[0] ?? "RESIDENT");
const actsAsArtist = ref(false);

const roleOptions = computed<SelectOption[]>(() =>
  props.roles.map((option) => ({ value: option, label: display.role(option) })),
);

/** Quem tatua por definição não precisa da caixa (RN 2.3). */
const asksAboutTattooing = computed(() => !artists.isAlways(role.value));

const tattoos = computed(() =>
  artists.includes(role.value, asksAboutTattooing.value ? actsAsArtist.value : false),
);

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
    password.value.length >= MINIMUM_PASSWORD &&
    (!tattoos.value || artistName.value.trim() !== ""),
);

function submit(): void {
  if (!ready.value) {
    return;
  }

  emit("submit", {
    email: email.value.trim(),
    password: password.value,
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
    title="New account"
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
        :disabled="props.busy"
      />
      <AppCheckbox
        v-if="asksAboutTattooing"
        v-model="actsAsArtist"
        label="Also tattoos, with their own schedule and payouts"
        :disabled="props.busy"
      />
      <AppInput
        v-model="password"
        label="Temporary password"
        type="password"
        required
        autocomplete="new-password"
        :error="passwordError"
        :disabled="props.busy"
      />

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
        Create account
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

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}
</style>
