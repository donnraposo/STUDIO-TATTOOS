<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import AppButton from "@/shared/components/AppButton.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import { useSession } from "@/shared/session/useSession";

/** Casca da aplicação: barra lateral escura e área de trabalho clara.
 *
 * A navegação é derivada do perfil, e isso é **aparência**: o item escondido
 * continua existindo como rota, e quem chegar nele pela URL é recusado pelo
 * backend com 403. Esconder é cortesia, não tranca.
 *
 * Lateral e não superior porque a lista de telas do MVP vai a nove itens
 * (`01_REGRAS_DE_NEGOCIO.md` §10) e uma barra no topo passaria a esconder
 * metade delas atrás de um menu logo na terceira sprint. */
interface NavigationItem {
  label: string;
  route: string;
  visible: boolean;
}

const ROLE_LABEL: Record<string, string> = {
  OWNER: "Owner",
  MANAGER: "Manager",
  RESIDENT: "Resident artist",
  GUEST: "Guest artist",
};

const { session, permissions } = useSession();
const router = useRouter();

const user = session.user;

const navigation = computed<NavigationItem[]>(() => {
  const current = user.value;
  if (!current) {
    return [];
  }

  return [
    { label: "Overview", route: "home", visible: true },
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
      <div class="brand">
        <img
          src="/brand/logo.jpg"
          alt=""
          class="mark"
        >
        <span class="brand-name">Studio</span>
      </div>

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

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.mark {
  width: var(--icon-box);
  height: var(--icon-box);
  border-radius: var(--radius-round);
  object-fit: cover;
}

.brand-name {
  font-weight: var(--weight-medium);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
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
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-round);
  color: var(--color-on-dark-muted);
  text-decoration: none;
}

nav a:hover {
  background: var(--color-ink-soft);
  color: var(--color-on-dark);
}

nav a.router-link-active {
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

@media (max-width: 64rem) {
  .shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-4);
  }

  nav {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .identity {
    padding-top: var(--space-0);
    border-top: none;
  }
}
</style>
