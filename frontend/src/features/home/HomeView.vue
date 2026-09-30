<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import PendingWorkList from "@/features/home/components/PendingWorkList.vue";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import HeroBanner from "@/shared/components/HeroBanner.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import type { PendingWorkItem } from "@/shared/domain/PendingWork";
import { useSession } from "@/shared/session/useSession";
import { usePendingWork } from "@/shared/work/usePendingWork";

/** Painel de entrada.
 *
 * **A área de pendências é o motivo desta tela existir** (RN-AGE-012 e seção
 * 10.1). Antes dela, descobrir que havia uma solicitação esperando exigia abrir
 * o calendário e reparar; quem não abrisse, não sabia.
 *
 * A tela **lê** o estado compartilhado, não o busca nem o inicia. Quem busca e
 * mantém atualizado é o `PendingWorkStore`, ligado pela casca — e a razão é o
 * contador da barra lateral, que precisa do mesmo número em qualquer tela,
 * inclusive nas que não são esta.
 *
 * Um `onMounted` daqui chamando o ciclo seria dois donos para a mesma coisa: a
 * casca monta antes, e a condição de quem decide já está resolvida lá.
 *
 * O gestor vê a área; residente e guest não. O painel deles é a M7.2.5, com o
 * recorte que a seção 10.2 descreve — mostrar aqui a fila do estúdio a quem não
 * decide seria ruído. */
const { session, permissions } = useSession();
const { pending } = usePendingWork();
const router = useRouter();

const user = session.user;

const isStaff = computed(() => (user.value ? permissions.isStaff(user.value) : false));

const waitingLabel = computed(() => {
  const total = pending.count.value;
  return total === 1 ? "1 item waiting" : `${total} items waiting`;
});

function open(item: PendingWorkItem): void {
  void router.push({ name: item.route });
}
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

    <section
      v-if="isStaff"
      class="waiting"
    >
      <header>
        <div>
          <SectionKicker label="Needs your decision" />
          <h2>{{ waitingLabel }}</h2>
        </div>
        <AppButton
          tone="ghost"
          :busy="pending.isLoading.value"
          @click="pending.refresh()"
        >
          Refresh
        </AppButton>
      </header>

      <LoadingState v-if="pending.isLoading.value && pending.count.value === 0" />

      <EmptyState
        v-else-if="pending.count.value === 0"
        title="Nothing waiting"
        description="Every request, deposit and quote has been decided."
      />

      <PendingWorkList
        v-else
        :items="[...pending.items.value]"
        @open="open"
      />
    </section>

    <HeroBanner
      kicker="Studio edition"
      title="The right space for remarkable work."
      description="Booths, clients and quotes in one place — with double booking made impossible."
    >
      <template #action>
        <AppButton
          tone="light"
          @click="router.push({ name: 'schedule' })"
        >
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
            <AppButton
              tone="ghost"
              @click="router.push({ name: 'schedule' })"
            >
              Open
            </AppButton>
          </template>
        </AppCard>

        <AppCard
          v-if="permissions.canSeeClients(user)"
          title="Clients"
        >
          <p>Register clients and keep their contact details current.</p>
          <template #footer>
            <AppButton
              tone="ghost"
              @click="router.push({ name: 'clients' })"
            >
              Open
            </AppButton>
          </template>
        </AppCard>

        <AppCard
          v-if="permissions.canSeeQuotes(user)"
          title="Quotes"
        >
          <p>Describe the work, plan sessions and get it approved.</p>
          <template #footer>
            <AppButton
              tone="ghost"
              @click="router.push({ name: 'quotes' })"
            >
              Open
            </AppButton>
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

.waiting {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.waiting header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
}

.waiting h2,
.operation h2 {
  font-size: var(--text-heading-1);
  letter-spacing: var(--tracking-display);
}

.operation {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(var(--track-card-min), 1fr));
  gap: var(--space-5);
  margin-top: var(--space-3);
}
</style>
