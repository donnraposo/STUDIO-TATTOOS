<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { BookingPlacement, type Placement } from "@/features/scheduling/BookingPlacement";
import BoothTimeline from "@/features/scheduling/components/BoothTimeline.vue";
import { useApi } from "@/shared/api/useApi";
import { useAsyncState } from "@/shared/async/useAsyncState";
import AppButton from "@/shared/components/AppButton.vue";
import AppInput from "@/shared/components/AppInput.vue";
import EmptyState from "@/shared/components/EmptyState.vue";
import ErrorState from "@/shared/components/ErrorState.vue";
import LoadingState from "@/shared/components/LoadingState.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import type { Booking, Booth } from "@/shared/domain/Booking";
import { StudioClock } from "@/shared/format/StudioClock";

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
}

interface DaySchedule {
  booths: Booth[];
  bookings: Booking[];
  namesByClient: Record<string, string>;
}

const { scheduling, clients: clientsApi } = useApi();
const clock = new StudioClock();
const placer = new BookingPlacement(OPENING_HOUR, CLOSING_HOUR, SLOT_MINUTES, clock);

const state = useAsyncState<DaySchedule>();
const day = ref(new Date().toISOString().slice(0, 10));
const selected = ref<Booking | null>(null);

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
    startsAt: withOffset(date, OPENING_HOUR, offsetMinutes),
    endsAt: withOffset(date, CLOSING_HOUR, offsetMinutes),
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

function withOffset(date: string, hour: number, offsetMinutes: number): string {
  const sign = offsetMinutes < 0 ? "-" : "+";
  const absolute = Math.abs(offsetMinutes);
  const hh = String(Math.floor(absolute / 60)).padStart(2, "0");
  const mm = String(absolute % 60).padStart(2, "0");
  return `${date}T${String(hour).padStart(2, "0")}:00:00${sign}${hh}:${mm}`;
}

async function load(): Promise<void> {
  const window = dayWindow(day.value);
  await state.run(async () => {
    const [booths, bookings] = await Promise.all([
      scheduling.listBooths(),
      scheduling.listBookings(window.startsAt, window.endsAt),
    ]);
    return { booths, bookings, namesByClient: await clientNames() };
  });
}

/** Falha em buscar nomes não derruba a agenda.
 *
 * O guest não acessa o cadastro de clientes e receberia 403 aqui. A agenda dele
 * precisa abrir do mesmo jeito — sem nome é menos informação, sem agenda é
 * tela quebrada. */
async function clientNames(): Promise<Record<string, string>> {
  try {
    const registered = await clientsApi.list();
    return Object.fromEntries(registered.map((client) => [client.id, client.name]));
  } catch {
    return {};
  }
}

const placedByBooth = computed<Record<string, PlacedBooking[]>>(() => {
  const schedule = state.data.value;
  if (!schedule) {
    return {};
  }

  const grouped: Record<string, PlacedBooking[]> = {};
  for (const booking of schedule.bookings) {
    const placement = placer.place(booking.startsAt, booking.endsAt);
    if (!placement) {
      continue;
    }
    const lane = grouped[booking.boothId] ?? [];
    lane.push({
      booking,
      placement,
      clientName: schedule.namesByClient[booking.clientId] ?? "Client",
      timeRange: `${clock.time(booking.startsAt)}–${clock.time(booking.endsAt)}`,
    });
    grouped[booking.boothId] = lane;
  }
  return grouped;
});

watch(day, load);
onMounted(load);
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
      @select="selected = $event"
    />

    <p
      v-if="selected"
      class="selection"
    >
      {{ selected.status }} · {{ clock.dateTime(selected.startsAt) }}
      <AppButton
        tone="ghost"
        @click="selected = null"
      >
        Clear
      </AppButton>
    </p>
  </div>
</template>

<style scoped>
.scheduling {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.selection {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
