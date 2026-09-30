<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { BookingPlacement, type Placement } from "@/features/scheduling/BookingPlacement";
import { ApiError } from "@/shared/api/ApiError";
import AppButton from "@/shared/components/AppButton.vue";
import BookingDecision from "@/features/scheduling/components/BookingDecision.vue";
import BookingForm, { type BookingDraft } from "@/features/scheduling/components/BookingForm.vue";
import { LanePacker } from "@/features/scheduling/LanePacker";
import BoothTimeline from "@/features/scheduling/components/BoothTimeline.vue";
import ConflictModal from "@/features/scheduling/components/ConflictModal.vue";
import { SchedulingClient } from "@/shared/api/SchedulingClient";
import { useApi } from "@/shared/api/useApi";
import { useAsyncState } from "@/shared/async/useAsyncState";
import AppInput from "@/shared/components/AppInput.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import ErrorState from "@/shared/components/ErrorState.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import type {
  Booking,
  BookingConflict,
  Booth,
  RejectionReason,
} from "@/shared/domain/Booking";
import type { Client } from "@/shared/domain/Client";
import type { StudioMember } from "@/shared/domain/StudioMember";
import { StudioClock } from "@/shared/format/StudioClock";
import { useSession } from "@/shared/session/useSession";

/** Agenda do dia: macas no eixo Y, horas no eixo X.
 *
 * O estúdio abre de terça a domingo, das 10h às 20h
 * (`01_REGRAS_DE_NEGOCIO.md` §1.1). A grade cobre esse expediente em faixas de
 * trinta minutos.
 *
 * **O nome do cliente é composto aqui, no cliente.** A API devolve
 * identificadores, e a tela cruza com a lista de clientes que ela já consome.
 * Não é gambiarra a desfazer: é junção sobre conjunto pequeno. O gatilho para
 * levá-la ao servidor é volume — quando a lista de clientes deixar de caber
 * numa requisição —, não estética.
 *
 * Quem não tem acesso ao cadastro de clientes, como o guest, vê o bloco sem
 * nome em vez de uma tela quebrada. */
const OPENING_HOUR = 10;
const CLOSING_HOUR = 20;
const SLOT_MINUTES = 30;

interface PlacedBooking {
  booking: Booking;
  placement: Placement;
  clientName: string;
  timeRange: string;
  /** Trilha dentro da maca. Solicitações concorrentes ficam em trilhas
   * diferentes para que ambas apareçam (RN-AGE-004). */
  track: number;
}

interface DaySchedule {
  booths: Booth[];
  bookings: Booking[];
  /** A lista inteira, e nao so um mapa de nomes: o formulario de nova reserva
   * precisa das mesmas pessoas para o seletor de cliente. Guardar as duas
   * coisas separadas faria a tela buscar clientes duas vezes. */
  clients: Client[];
  artists: StudioMember[];
}

const DAY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

/** Aceita só o que é uma data, e ignora o resto em silêncio.
 *
 * O endereço é digitável, e `?day=ontem` não pode virar uma agenda vazia sem
 * explicação: o dia de hoje é resposta melhor do que uma tela que não carrega. */
function readDay(value: unknown): string | null {
  return typeof value === "string" && DAY_PATTERN.test(value) ? value : null;
}

const { scheduling, clients: clientsApi, accounts } = useApi();
const { session, permissions } = useSession();
const route = useRoute();
const router = useRouter();
const clock = new StudioClock();
const placer = new BookingPlacement(OPENING_HOUR, CLOSING_HOUR, SLOT_MINUTES, clock);
const packer = new LanePacker();

const state = useAsyncState<DaySchedule>();
/** O dia aberto. Vem do endereço quando alguém chega por um item do painel, e
 * é o dia do estúdio quando não vem — nunca o do navegador.
 *
 * `toISOString().slice(0, 10)` dava o dia em **UTC**: às 00h30 de Dublin no
 * verão irlandês, a agenda abria no dia anterior. Uma hora de largura, só de
 * madrugada e só em parte do ano — o tipo de defeito que ninguém reproduz
 * quando é relatado. */
const day = ref(readDay(route.query.day) ?? clock.today());
const selected = ref<Booking | null>(null);
const conflict = ref<BookingConflict | null>(null);
const composing = ref(false);
const deciding = ref(false);
const decisionFailure = ref<string | null>(null);

const heading = computed(() => {
  const schedule = state.data.value;
  if (!schedule) {
    return "Schedule";
  }
  return `${schedule.bookings.length} booking${schedule.bookings.length === 1 ? "" : "s"}`;
});

/** A janela vai da abertura ao fechamento, no fuso do estúdio.
 *
 * O deslocamento é montado a partir da própria data para que o dia pedido ao
 * servidor seja o dia do estúdio, e não o do navegador — sem isso, um artista
 * em outro fuso veria a agenda de ontem ou de amanhã. */
function dayWindow(date: string): { startsAt: string; endsAt: string } {
  const opening = new Date(`${date}T00:00:00Z`);
  const offsetMinutes = offsetAt(opening);
  return {
    startsAt: withOffset(date, `${String(OPENING_HOUR).padStart(2, "0")}:00`, offsetMinutes),
    endsAt: withOffset(date, `${String(CLOSING_HOUR).padStart(2, "0")}:00`, offsetMinutes),
  };
}

/** Deslocamento do estúdio, em minutos, na data informada. Muda com o horário
 * de verão, então precisa ser calculado por dia e não fixado. */
function offsetAt(date: Date): number {
  const readAsStudio = new Date(
    date.toLocaleString("en-US", { timeZone: StudioClock.TIME_ZONE }),
  );
  const readAsUtc = new Date(date.toLocaleString("en-US", { timeZone: "UTC" }));
  return Math.round((readAsStudio.getTime() - readAsUtc.getTime()) / 60000);
}

/** Monta o instante ISO no fuso do estúdio a partir de `HH:MM`.
 *
 * O deslocamento vem calculado para a data em questão, e não fixado: o horário
 * de verão irlandês muda duas vezes por ano, e uma reserva marcada com o
 * deslocamento errado cairia uma hora fora sem ninguém notar. */
function withOffset(date: string, time: string, offsetMinutes: number): string {
  const sign = offsetMinutes < 0 ? "-" : "+";
  const absolute = Math.abs(offsetMinutes);
  const hh = String(Math.floor(absolute / 60)).padStart(2, "0");
  const mm = String(absolute % 60).padStart(2, "0");
  return `${date}T${time}:00${sign}${hh}:${mm}`;
}

async function load(): Promise<void> {
  const window = dayWindow(day.value);
  await state.run(async () => {
    const [booths, bookings] = await Promise.all([
      scheduling.listBooths(),
      scheduling.listBookings(window.startsAt, window.endsAt),
    ]);
    return { booths, bookings, clients: await visibleClients(), artists: await bookableArtists() };
  });
}

/** Falha em buscar clientes não derruba a agenda.
 *
 * O guest não acessa o cadastro e receberia 403 aqui. A agenda dele precisa
 * abrir do mesmo jeito — sem nome é menos informação, sem agenda é tela
 * quebrada. */
async function visibleClients(): Promise<Client[]> {
  try {
    return await clientsApi.list();
  } catch {
    return [];
  }
}

/** Só o gestor lista contas; os demais recebem 403 e agendam para si mesmos,
 * que é o caso em que o seletor de artista nem aparece. */
async function bookableArtists(): Promise<StudioMember[]> {
  try {
    return await accounts.listArtists();
  } catch {
    return [];
  }
}

const namesByClient = computed<Record<string, string>>(() =>
  Object.fromEntries((state.data.value?.clients ?? []).map((client) => [client.id, client.name])),
);

const placedByBooth = computed<Record<string, PlacedBooking[]>>(() => {
  const schedule = state.data.value;
  if (!schedule) {
    return {};
  }

  const grouped: Record<string, Omit<PlacedBooking, "track">[]> = {};
  for (const booking of schedule.bookings) {
    const placement = placer.place(booking.startsAt, booking.endsAt);
    if (!placement) {
      continue;
    }
    const lane = grouped[booking.boothId] ?? [];
    lane.push({
      booking,
      placement,
      clientName: namesByClient.value[booking.clientId] ?? "Client",
      timeRange: `${clock.time(booking.startsAt)}–${clock.time(booking.endsAt)}`,
    });
    grouped[booking.boothId] = lane;
  }

  return Object.fromEntries(
    Object.entries(grouped).map(([boothId, lane]) => [
      boothId,
      packer
        .pack(lane, (entry) => entry.placement)
        .map(({ item, track }) => ({ ...item, track })),
    ]),
  );
});

/** Quantas trilhas cada maca precisa, para a linha crescer o suficiente. */
const tracksByBooth = computed<Record<string, number>>(() =>
  Object.fromEntries(
    Object.entries(placedByBooth.value).map(([boothId, lane]) => [
      boothId,
      lane.reduce((highest, entry) => Math.max(highest, entry.track + 1), 1),
    ]),
  ),
);

const canDecide = computed(() =>
  session.user.value ? permissions.canDecide(session.user.value) : false,
);

/** O agendamento que já ocupava o horário, quando ele está na tela.
 *
 * Pode não estar: o conflito pode ser com a agenda de outro artista, que este
 * usuário não tem permissão para ver. O modal trata os dois casos — ocultar a
 * existência do conflito seria pior do que admitir que não se pode mostrá-lo. */
const conflicting = computed<Booking | null>(() => {
  const id = conflict.value?.conflictingBookingId;
  return id ? (state.data.value?.bookings.find((booking) => booking.id === id) ?? null) : null;
});

const conflictingLabel = computed<string | null>(() => {
  const booking = conflicting.value;
  if (!booking) {
    return null;
  }
  const name = namesByClient.value[booking.clientId] ?? "Client";
  return `${name} · ${clock.time(booking.startsAt)}–${clock.time(booking.endsAt)}`;
});

const selectedLabel = computed(() => {
  const booking = selected.value;
  if (!booking) {
    return { clientName: "", timeRange: "" };
  }
  return {
    clientName: namesByClient.value[booking.clientId] ?? "Client",
    timeRange: `${clock.time(booking.startsAt)}–${clock.time(booking.endsAt)}`,
  };
});

/** Todas as decisões compartilham o mesmo envelope: ocupado, limpa erro, tenta,
 * e em caso de conflito abre o modal da RN-AGE-007 em vez de mostrar texto de
 * erro. Aprovar, recusar, cancelar e remarcar passam por aqui. */
async function decide(action: () => Promise<unknown>): Promise<void> {
  deciding.value = true;
  decisionFailure.value = null;
  try {
    await action();
    selected.value = null;
    composing.value = false;
    await load();
  } catch (error) {
    const clash = SchedulingClient.conflictFrom(error);
    if (clash) {
      selected.value = null;
      composing.value = false;
      conflict.value = clash;
      return;
    }
    decisionFailure.value =
      error instanceof ApiError ? error.message : "Could not reach the studio system.";
  } finally {
    deciding.value = false;
  }
}

async function create(draft: BookingDraft): Promise<void> {
  const offsetMinutes = offsetAt(new Date(`${day.value}T00:00:00Z`));
  await decide(() =>
    scheduling.create({
      clientId: draft.clientId,
      boothId: draft.boothId,
      startsAt: withOffset(day.value, draft.startTime, offsetMinutes),
      endsAt: withOffset(day.value, draft.endTime, offsetMinutes),
      artistId: draft.artistId,
      approveImmediately: draft.approveImmediately,
    }),
  );
}

async function approve(): Promise<void> {
  const booking = selected.value;
  if (booking) {
    await decide(() => scheduling.approve(booking.id));
  }
}

async function reject(reason: RejectionReason, note: string | null): Promise<void> {
  const booking = selected.value;
  if (booking) {
    await decide(() => scheduling.reject(booking.id, reason, note));
  }
}

/** Cancelamento e não comparecimento (RN-AGE-009 e RN-AGE-010). */
async function cancel(reason: string, noShow: boolean): Promise<void> {
  const booking = selected.value;
  if (booking) {
    await decide(() => scheduling.cancel(booking.id, reason, noShow));
  }
}

/** Remarcação (RN-AGE-008). O novo intervalo passa pelas mesmas restrições do
 * banco, então um 409 aqui cai no mesmo modal de conflito das demais ações. */
async function reschedule(
  startTime: string,
  endTime: string,
  boothId: string | null,
): Promise<void> {
  const booking = selected.value;
  if (!booking) {
    return;
  }
  const offsetMinutes = offsetAt(new Date(`${day.value}T00:00:00Z`));
  await decide(() =>
    scheduling.reschedule(
      booking.id,
      withOffset(day.value, startTime, offsetMinutes),
      withOffset(day.value, endTime, offsetMinutes),
      boothId,
    ),
  );
}

function startComposing(): void {
  decisionFailure.value = null;
  composing.value = true;
}

/** O dia aberto fica no endereço, para que recarregar não perca a página e o
 * endereço possa ser copiado para outra pessoa.
 *
 * `replace` e não `push` **de propósito**: cada dia consultado viraria uma
 * entrada no histórico, e sair da agenda passaria a exigir um toque em voltar
 * para cada dia que se olhou. Com `replace`, voltar leva de onde se veio — o
 * painel, quando foi ele que trouxe. */
function rememberDay(current: string): void {
  if (route.query.day !== current) {
    void router.replace({ query: { ...route.query, day: current } });
  }
}

watch(day, (current) => {
  void load();
  rememberDay(current);
});

/** Chegar por um item do painel com a tela já aberta também muda o dia. */
watch(
  () => route.query.day,
  (value) => {
    const requested = readDay(value);
    if (requested && requested !== day.value) {
      day.value = requested;
    }
  },
);

/** Na montagem o endereço também é acertado.
 *
 * Um `?day=ontem` cai no dia de hoje, e sem isto a barra continuaria exibindo
 * `ontem` sobre uma agenda que é de hoje — o endereço passaria a mentir sobre o
 * que está na tela, e copiá-lo levaria outra pessoa ao mesmo engano. */
onMounted(() => {
  void load();
  rememberDay(day.value);
});
</script>

<template>
  <div class="scheduling">
    <PageHeader
      kicker="Studio workspace"
      :title="heading"
    >
      <template #actions>
        <AppInput
          v-model="day"
          label="Day"
          type="date"
        />
        <AppButton
          :disabled="state.isLoading.value"
          @click="startComposing"
        >
          New booking
        </AppButton>
      </template>
    </PageHeader>

    <LoadingState v-if="state.isLoading.value" />

    <ErrorState
      v-else-if="state.error.value"
      :message="state.errorMessage.value"
      :retryable="state.isRetryable.value"
      @retry="state.retry()"
    />

    <EmptyState
      v-else-if="state.data.value && state.data.value.booths.length === 0"
      title="No booths yet"
      description="The studio management adds booths before the schedule can be used."
    />

    <BoothTimeline
      v-else-if="state.data.value"
      :booths="state.data.value.booths"
      :placer="placer"
      :placed-by-booth="placedByBooth"
      :tracks-by-booth="tracksByBooth"
      @select="selected = $event"
    />

    <BookingForm
      v-if="composing && state.data.value"
      :day="day"
      :clients="state.data.value.clients"
      :booths="state.data.value.booths"
      :artists="state.data.value.artists"
      :can-decide="canDecide"
      :busy="deciding"
      :failure="decisionFailure"
      @submit="create"
      @close="composing = false"
    />

    <BookingDecision
      v-if="selected"
      :booking="selected"
      :client-name="selectedLabel.clientName"
      :time-range="selectedLabel.timeRange"
      :requested-at="clock.dateTime(selected.requestedAt)"
      :booths="state.data.value?.booths ?? []"
      :can-decide="canDecide"
      :busy="deciding"
      :failure="decisionFailure"
      @approve="approve"
      @reject="reject"
      @cancel="cancel"
      @reschedule="reschedule"
      @close="selected = null"
    />

    <ConflictModal
      v-if="conflict"
      :scope="conflict.scope"
      :message="conflict.message"
      :existing="conflicting"
      :existing-label="conflictingLabel"
      @acknowledge="conflict = null"
    />
  </div>
</template>

<style scoped>
.scheduling {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
</style>
