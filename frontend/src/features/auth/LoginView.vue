<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { ApiError } from "@/shared/api/ApiError";
import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import BrandLockup from "@/shared/components/BrandLockup.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import { useSession } from "@/shared/session/useSession";

const { session } = useSession();
const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");
const failure = ref<string | null>(null);
const busy = ref(false);

/** O backend responde a mesma coisa para senha errada e e-mail inexistente, de
 * propósito (RN 2.7), e até o tempo de resposta é equalizado. A tela respeita
 * isso: não tenta adivinhar qual foi o caso nem oferece "e-mail não
 * cadastrado", o que entregaria de volta o que o backend escondeu. */
async function submit(): Promise<void> {
  busy.value = true;
  failure.value = null;
  try {
    await session.signIn(email.value, password.value);
    const target = route.query.redirect;
    await router.replace(typeof target === "string" ? target : { name: "home" });
  } catch (error) {
    failure.value =
      error instanceof ApiError ? error.message : "Could not reach the studio system.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <main class="login">
    <!--
      Lado da marca. Não há autocadastro no sistema (a F5 trata disso), então
      esta metade não vende nada: ela diz de quem é o sistema em que a pessoa
      está entrando, e é a única tela onde a marca aparece em tamanho grande.
    -->
    <aside class="brand-side">
      <BrandLockup
        name="Tattoo Studio"
        size="large"
      />

      <div class="statement">
        <SectionKicker
          label="Cork City · Studio operations"
          on-dark
        />
        <h1>The studio, in order.</h1>
        <p>Benches, clients, quotes and payouts — kept straight so the work can breathe.</p>
      </div>

      <p class="edition">
        Internal system
      </p>
    </aside>

    <section class="form-side">
      <form
        class="panel"
        @submit.prevent="submit"
      >
        <SectionKicker label="Private workspace" />
        <h2>Welcome back.</h2>
        <p class="lead">
          Sign in with your studio account.
        </p>

        <AppInput
          v-model="email"
          label="Email"
          type="email"
          autocomplete="username"
          required
          :disabled="busy"
        />
        <AppInput
          v-model="password"
          label="Password"
          type="password"
          autocomplete="current-password"
          required
          :disabled="busy"
        />

        <p
          v-if="failure"
          class="failure"
          role="alert"
        >
          {{ failure }}
        </p>

        <AppButton
          type="submit"
          block
          :busy="busy"
        >
          {{ busy ? "Signing in…" : "Sign in" }}
        </AppButton>

        <p class="note">
          Accounts are created by the studio management.
        </p>
      </form>
    </section>
  </main>
</template>

<style scoped>
.login {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: var(--viewport-height);
}

.brand-side {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: var(--space-10);
  padding: var(--space-12) var(--space-10);
  background-color: var(--color-black);
  background-image: var(--overlay-media-panel), var(--image-studio);
  background-position: center;
  background-size: cover;
  color: var(--color-on-dark);
}




.statement {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: var(--content-measure);
}

.statement h1 {
  font-size: var(--text-display-1);
  letter-spacing: var(--tracking-display);
  line-height: var(--line-display);
}

.statement p {
  color: var(--color-on-dark-muted);
  font-size: var(--text-label-1);
}

.edition {
  color: var(--color-on-dark-muted);
  font-size: var(--text-kicker);
  letter-spacing: var(--tracking-kicker);
  text-transform: uppercase;
}

.form-side {
  display: grid;
  place-items: center;
  padding: var(--space-page);
  background: var(--color-canvas);
}

.panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  width: 100%;
  max-width: var(--content-measure);
}

.panel h2 {
  font-size: var(--text-display-2);
  letter-spacing: var(--tracking-display);
  line-height: var(--line-display);
}

.lead {
  margin-bottom: var(--space-4);
  color: var(--color-muted);
}

.failure {
  color: var(--color-danger);
  font-size: var(--text-label-3);
}

.note {
  color: var(--color-muted);
  font-size: var(--text-label-3);
  text-align: center;
}

/* No celular a metade da marca vira uma faixa curta no topo: mantém a
   identidade sem empurrar o formulário para fora da primeira dobra. */
@media (max-width: 64rem) {
  .login {
    grid-template-columns: 1fr;
  }

  .brand-side {
    gap: var(--space-6);
    padding: var(--space-8) var(--space-page);
  }

  .statement h1 {
    font-size: var(--text-heading-1);
  }

  .statement p,
  .edition {
    display: none;
  }
}
</style>
