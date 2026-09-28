<script setup lang="ts">
import AppCard from "@/shared/components/AppCard.vue";
import AppButton from "@/shared/components/AppButton.vue";
import HeroBanner from "@/shared/components/HeroBanner.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import { useSession } from "@/shared/session/useSession";

/** Entrada provisória, até a M7.1.3.
 *
 * A tela de entrada definida para o MVP é a **agenda do dia**, que ainda não
 * existe. Até lá, esta apresenta o espaço de trabalho sem fingir número nenhum:
 * um painel com indicadores zerados ou inventados seria pior do que não ter
 * painel, porque numa demonstração ninguém pergunta se o número é real. */
const { session, permissions } = useSession();
const user = session.user;
</script>

<template>
  <div
    v-if="user"
    class="home"
  >
    <PageHeader
      kicker="Studio workspace"
      :title="`Good to see you, ${user.fullName.split(' ')[0]}.`"
    />

    <HeroBanner
      kicker="Studio edition"
      title="The right space for remarkable work."
      description="Booths, clients and quotes in one place — with double booking made impossible."
    >
      <template #action>
        <AppButton tone="light">
          Open today's schedule
        </AppButton>
      </template>
    </HeroBanner>

    <section class="operation">
      <SectionKicker label="Workspace" />
      <h2>Your operation</h2>

      <div class="cards">
        <AppCard title="Schedule">
          <p>Booth timeline, requests and conflict prevention.</p>
          <template #footer>
            <StatusBadge
              label="Coming next"
              tone="warning"
            />
          </template>
        </AppCard>

        <AppCard
          v-if="permissions.canSeeClients(user)"
          title="Clients"
        >
          <p>Register clients and keep their contact details current.</p>
          <template #footer>
            <StatusBadge
              label="Coming next"
              tone="warning"
            />
          </template>
        </AppCard>

        <AppCard
          v-if="permissions.canSeeQuotes(user)"
          title="Quotes"
        >
          <p>Describe the work, plan sessions and get it approved.</p>
          <template #footer>
            <StatusBadge
              label="Coming next"
              tone="warning"
            />
          </template>
        </AppCard>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.operation {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.operation h2 {
  font-size: var(--text-heading-1);
  letter-spacing: var(--tracking-display);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(var(--track-card-min), 1fr));
  gap: var(--space-5);
  margin-top: var(--space-3);
}
</style>
