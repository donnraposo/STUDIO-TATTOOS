<script setup lang="ts">
import { computed, watch } from "vue";
import { useRouter } from "vue-router";

import AppBadgeCount from "@/shared/components/AppBadgeCount.vue";
import AppButton from "@/shared/components/AppButton.vue";
import BrandLockup from "@/shared/components/BrandLockup.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import { useSession } from "@/shared/session/useSession";
import { usePendingWork } from "@/shared/work/usePendingWork";

/** Casca da aplicação: barra lateral escura e área de trabalho clara.
 *
 * A navegação é derivada do perfil, e isso é **aparência**: o item escondido
 * continua existindo como rota, e quem chegar nele pela URL é recusado pelo
 * backend com 403. Esconder é cortesia, não tranca.
 *
 * Lateral e não superior porque a lista de telas do MVP vai a nove itens
 * (`01_REGRAS_DE_NEGOCIO.md` §10) e uma barra no topo passaria a esconder
 * metade delas atrás de um menu logo na terceira sprint.
 *
 * **O contador de pendências mora aqui, e é o ponto** (RN-AGE-012). A área no
 * painel ajuda quem já está no painel; o problema relatado pelo estúdio é
 * justamente não estar — o gerente precisava abrir o calendário para descobrir
 * que havia uma solicitação esperando. Na lateral, o número acompanha quem
 * decide, esteja em que tela estiver.
 *
 * A casca **lê** o estado compartilhado e não chama a API: quem busca é o
 * `PendingWorkStore`, pela mesma razão que a sessão vive num estado único. */
interface NavigationItem {
  label: string;
  route: string;
  visible: boolean;
  /** Quantos itens esperam decisão nesta tela. Zero não desenha nada. */
  waiting?: number;
}

const ROLE_LABEL: Record<string, string> = {
  OWNER: "Owner",
  MANAGER: "Manager",
  RESIDENT: "Resident artist",
  GUEST: "Guest artist",
};

const { session, permissions } = useSession();
const { pending } = usePendingWork();
const router = useRouter();

const user = session.user;

const isStaff = computed(() => (user.value ? permissions.isStaff(user.value) : false));

/** O ciclo começa quando há alguém que decide, e para quando ele sai.
 *
 * Ligado aqui e não na entrada da aplicação porque é aqui que se sabe quem
 * entrou: o residente não vê a fila do estúdio, e buscá-la para ele seria pedir
 * ao servidor um 403 por minuto. */
watch(
  isStaff,
  (decides) => {
    if (decides) {
      pending.start();
    } else {
      pending.stop();
    }
  },
  { immediate: true },
);

const navigation = computed<NavigationItem[]>(() => {
  const current = user.value;
  if (!current) {
    return [];
  }

  return [
    { label: "Overview", route: "home", visible: true, waiting: pending.count.value },
    { label: "Schedule", route: "schedule", visible: true },
    { label: "Clients", route: "clients", visible: permissions.canSeeClients(current) },
    { label: "Quotes", route: "quotes", visible: permissions.canSeeQuotes(current) },
    { label: "Payments", route: "payments", visible: permissions.canDecide(current) },
    { label: "Payouts", route: "payouts", visible: permissions.canSeePayouts(current) },
    { label: "Revenue", route: "revenue", visible: permissions.isStaff(current) },
    {
      label: "Accounts",
      route: "accounts",
      visible: permissions.canManageAccounts(current),
    },
    { label: "System", route: "status", visible: permissions.isStaff(current) },
  ].filter((item) => item.visible);
});

const roleLabel = computed(() => (user.value ? (ROLE_LABEL[user.value.role] ?? "") : ""));
const initial = computed(() => user.value?.fullName.trim().charAt(0).toUpperCase() ?? "");

async function signOut(): Promise<void> {
  await session.signOut();
  await router.replace({ name: "login" });
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <BrandLockup name="Studio" />

      <SectionKicker
        label="Studio workspace"
        on-dark
      />

      <nav aria-label="Main">
        <RouterLink
          v-for="item in navigation"
          :key="item.label"
          :to="{ name: item.route }"
        >
          {{ item.label }}
          <AppBadgeCount
            v-if="item.waiting"
            :count="item.waiting"
            label="items waiting for a decision"
          />
        </RouterLink>
      </nav>

      <div
        v-if="user"
        class="identity"
      >
        <span
          class="avatar"
          aria-hidden="true"
        >{{ initial }}</span>
        <span class="who">
          <strong>{{ user.fullName }}</strong>
          <small>{{ roleLabel }}</small>
        </span>
      </div>
    </aside>

    <div class="workspace">
      <div class="topline">
        <AppButton
          tone="ghost"
          @click="signOut"
        >
          Sign out
        </AppButton>
      </div>
      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: var(--viewport-height);
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-6) var(--space-5);
  background: var(--color-ink);
  color: var(--color-on-dark);
}




nav {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--space-1);
}

/* Item ativo em pílula, como na referência: a marcação é a forma, e o ouro
   entra só no texto. Uma pílula inteiramente dourada roubaria a atenção do
   conteúdo a cada tela. */
nav a {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-round);
  color: var(--color-on-dark-muted);
  text-decoration: none;
}

nav a:hover {
  background: var(--color-ink-soft);
  color: var(--color-on-dark);
}

/* `exact-active` e nao `active`: a rota raiz e prefixo de todas as outras, e
   com a classe comum o item "Overview" ficava aceso em cima de qualquer tela
   -- dois itens marcados ao mesmo tempo, e nenhum deles dizendo onde voce
   esta. */
nav a.router-link-exact-active {
  background: var(--color-ink-soft);
  color: var(--color-gold-bright);
  font-weight: var(--weight-medium);
}

.identity {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding-top: var(--space-5);
  border-top: var(--border-dark);
}

.avatar {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: var(--icon-box);
  height: var(--icon-box);
  border-radius: var(--radius-round);
  background: var(--gradient-gold);
  color: var(--color-ink);
  font-weight: var(--weight-medium);
}

.who {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.who strong {
  overflow: hidden;
  font-weight: var(--weight-medium);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.who small {
  color: var(--color-on-dark-muted);
  font-size: var(--text-label-3);
}

.workspace {
  display: flex;
  flex-direction: column;
  background: var(--color-canvas);
}

.topline {
  display: flex;
  justify-content: flex-end;
  padding: var(--space-5) var(--space-page) var(--space-0);
}

.content {
  flex: 1;
  padding: var(--space-5) var(--space-page) var(--space-12);
}

/* Tablet e celular: a lateral vira barra no topo. A navegacao rola na
   horizontal em vez de quebrar em varias linhas -- quatro itens ja empurrariam
   o conteudo para baixo da dobra num telefone. */
@media (max-width: 64rem) {
  .shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: sticky;
    top: var(--space-0);
    z-index: var(--layer-sticky);
    display: grid;
    grid-template-areas: "brand identity" "nav nav";
    grid-template-columns: 1fr auto;
    gap: var(--space-3);
    padding: var(--space-3) var(--space-page);
  }

  .brand {
    grid-area: brand;
  }

  .identity {
    grid-area: identity;
    padding-top: var(--space-0);
    border-top: none;
  }

  nav {
    grid-area: nav;
    flex: none;
    flex-direction: row;
    overflow-x: auto;
    gap: var(--space-2);
  }

  nav a {
    flex-shrink: 0;
    padding: var(--space-2) var(--space-4);
  }

  /* O rotulo da secao e o nome completo saem: no celular eles custam altura e
     nao dizem nada que o avatar e o proprio menu ja nao digam. */
  .sidebar > p,
  .who {
    display: none;
  }

  .topline {
    padding: var(--space-4) var(--space-page) var(--space-0);
  }
}

</style>
