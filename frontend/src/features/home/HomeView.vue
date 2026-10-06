<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import ArtistPanel from "@/features/home/components/ArtistPanel.vue";
import PendingWorkList from "@/features/home/components/PendingWorkList.vue";
import { useApi } from "@/shared/api/useApi";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import HeroBanner from "@/shared/components/HeroBanner.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import SectionKicker from "@/shared/components/SectionKicker.vue";
import type { Booking } from "@/shared/domain/Booking";
import type { Payout } from "@/shared/domain/Payout";
import type { PendingWorkItem } from "@/shared/domain/PendingWork";
import type { Quote } from "@/shared/domain/Quote";
import { ArtistRole } from "@/shared/domain/ArtistRole";
import { StudioClock } from "@/shared/format/StudioClock";
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
 * **O gestor vê a fila; quem tatua vê o próprio dia** (seções 10.1, 10.2 e
 * 10.3). São perguntas diferentes: a fila é trabalho a fazer, o painel do
 * artista é o que vem pela frente e o que está parado esperando o estúdio.
 * Mostrar a fila do estúdio a quem não decide seria ruído, e esconder o dia de
 * quem atende deixaria a tela de entrada sem conteúdo para metade da equipe.
 *
 * O proprietário que tatua vê **os dois**, e é correto: a alçada administrativa
 * não o tira da maca.
 *
 * **Esta tela busca o painel do artista, e não busca a fila.** A fila mora no
 * `PendingWorkStore` porque o contador da barra lateral precisa do mesmo número
 * em qualquer tela; o painel do artista só existe aqui, e um estado
 * compartilhado para um único leitor seria cerimônia.
 *
 * **O nome do cliente encaminhado é buscado à parte** (RN-CLI-004): a lista de
 * clientes traz só os que o artista cadastrou, e o resto do dia dele ficaria
 * sem nome. A regra manda mostrá-lo dentro do agendamento, e é o que se faz.
 *
 * **O que a seção 10.2 pede e ainda não existe:** o repasse **previsto** da
 * semana corrente — só há fechamento de sexta (RN-REP-004) — e o pós-venda, que
 * é da Fase 2. A seção 10.3 pede ainda as semanas pagas do guest, que dependem
 * da tabela `guest_week`. Nada disso é inventado aqui: o cartão mostra o último
 * repasse **fechado** e diz que é isso. */
interface ArtistDay {
  bookings: Booking[];
  quotes: Quote[];
  payouts: Payout[];
  clientNames: Record<string, string>;
}

const { session, permissions } = useSession();
const { pending } = usePendingWork();
const { scheduling, quotes: quotesApi, payouts: payoutsApi, clients } = useApi();
const router = useRouter();

const artists = new ArtistRole();
const clock = new StudioClock();

const user = session.user;
const day = ref<ArtistDay | null>(null);
const now = ref(new Date().toISOString());

const isStaff = computed(() => (user.value ? permissions.isStaff(user.value) : false));

const tattoos = computed(() =>
  user.value ? artists.includes(user.value.role, user.value.actsAsArtist) : false,
);

const showQuotes = computed(() => (user.value ? permissions.canSeeQuotes(user.value) : false));

/** Cada peça falha por conta própria e devolve vazio.
 *
 * O painel do guest é o motivo: ele não acessa orçamentos (RN-ORC-001) nem tem
 * cadastro de clientes (RN-GST-004), e o servidor responde 403 nos dois. Uma
 * busca conjunta derrubaria a tela inteira por causa de duas recusas corretas —
 * e o guest ficaria sem ver a própria agenda. */
async function loadDay(): Promise<void> {
  if (!tattoos.value) {
    return;
  }

  const today = clock.today();
  const [bookings, ownQuotes, payouts, clientList] = await Promise.all([
    or(() => scheduling.listBookings(`${today}T00:00:00Z`, `${today}T23:59:59Z`), []),
    or(() => (showQuotes.value ? quotesApi.list() : Promise.resolve([])), []),
    or(() => payoutsApi.list(), []),
    or(() => clients.list(), []),
  ]);

  const named: Record<string, string> = Object.fromEntries(
    clientList.map((client) => [client.id, client.name]),
  );

  now.value = new Date().toISOString();
  day.value = {
    bookings,
    quotes: ownQuotes,
    payouts,
    clientNames: { ...named, ...(await referredNames(bookings, named)) },
  };
}

/** Os nomes que faltam, buscados um a um (RN-CLI-004).
 *
 * A regra é explícita: quando o estúdio encaminha a um artista o cliente de
 * outro, ele vê **nome, telefone e Instagram dentro do próprio agendamento**. A
 * lista de clientes não os traz — e corretamente, porque lá a regra é o cadastro
 * completo, que continua sendo só de quem cadastrou.
 *
 * Sem isto o artista abria o painel e lia "Client" no horário das 11h: a agenda
 * dele dizendo que alguém vem sem dizer quem.
 *
 * Uma requisição por cliente desconhecido do dia — poucos, e só os que faltam.
 * Se um dia a agenda do artista tiver dezenas de clientes alheios num só dia, o
 * gatilho para levar a junção ao servidor é esse, não a estética. */
async function referredNames(
  bookings: Booking[],
  known: Record<string, string>,
): Promise<Record<string, string>> {
  const missing = [...new Set(bookings.map((booking) => booking.clientId))].filter(
    (id) => !(id in known),
  );

  const found = await Promise.all(
    missing.map(async (id) => [id, (await or(() => clients.find(id), null))?.name] as const),
  );

  return Object.fromEntries(
    found.filter((entry): entry is readonly [string, string] => Boolean(entry[1])),
  );
}

async function or<T>(load: () => Promise<T>, fallback: T): Promise<T> {
  try {
    return await load();
  } catch {
    return fallback;
  }
}

onMounted(loadDay);

const waitingLabel = computed(() => {
  const total = pending.count.value;
  return total === 1 ? "1 item waiting" : `${total} items waiting`;
});

/** Abre o item no lugar exato, e não só na tela certa.
 *
 * A agenda de um agendamento de outra semana é a daquela semana: levar ao dia
 * de hoje devolveria a procura ao gestor, que é justamente o que esta área
 * existe para acabar. */
function open(item: PendingWorkItem): void {
  void router.push({ name: item.route, query: item.query });
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

    <ArtistPanel
      v-if="tattoos && day"
      :bookings="day.bookings"
      :quotes="day.quotes"
      :payouts="day.payouts"
      :client-names="day.clientNames"
      :show-quotes="showQuotes"
      :now="now"
      @open="router.push({ name: $event })"
    />

    <HeroBanner
      kicker="Studio edition"
      title="The right space for remarkable work."
      description="Benches, clients and quotes in one place — with double booking made impossible."
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
          <p>Bench timeline, requests and conflict prevention.</p>
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
