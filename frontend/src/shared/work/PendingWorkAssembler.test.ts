import { describe, expect, it } from "vitest";

import type { Booking } from "@/shared/domain/Booking";
import type { Payment } from "@/shared/domain/Payment";
import type { Quote } from "@/shared/domain/Quote";
import { PendingWorkAssembler } from "@/shared/work/PendingWorkAssembler";

/** A fila do painel do gestor (RN-AGE-012 e seção 10.1).
 *
 * O que importa aqui é a **ordem**. Uma fila ordenada pelo mais recente mostra
 * primeiro o que acabou de chegar e empurra para o fim o que está parado — o
 * contrário do que a área existe para fazer. É o tipo de defeito que ninguém vê
 * numa tela com três itens e que custa uma solicitação esquecida numa com
 * trinta.
 */

function booking(overrides: Partial<Booking> = {}): Booking {
  return {
    id: "b1",
    clientId: "c1",
    artistId: "a1",
    benchId: "bench1",
    startsAt: "2026-10-06T10:00:00+01:00",
    endsAt: "2026-10-06T12:00:00+01:00",
    status: "REQUESTED",
    requestedAt: "2026-10-01T09:00:00+01:00",
    rejectionReason: null,
    rejectionNote: null,
    ...overrides,
  };
}

function payment(overrides: Partial<Payment> = {}): Payment {
  return {
    id: "p1",
    bookingId: "b1",
    sessionId: null,
    clientId: "c1",
    amount: "50.00",
    kind: "DEPOSIT",
    method: "BANK_TRANSFER",
    status: "REPORTED",
    note: null,
    reportedAt: "2026-10-02T09:00:00+01:00",
    confirmedAt: null,
    refusedAt: null,
    refusalReason: null,
    retainedAt: null,
    retainedReason: null,
    ...overrides,
  };
}

function quote(overrides: Partial<Quote> = {}): Quote {
  return {
    id: "q1",
    clientId: "c1",
    artistId: "a1",
    origin: "ARTIST_OWN",
    description: "Blackwork forearm sleeve",
    bodyRegion: "Left forearm",
    sizeEstimate: "20cm",
    totalValue: "1000.00",
    plannedSessions: 4,
    plannedValuePerSession: "250.00",
    estimatedDurationMinutes: 180,
    notes: null,
    status: "PENDING",
    artistPercentage: null,
    approvedAt: null,
    rejectionReason: null,
    rejectionNote: null,
    createdAt: "2026-10-03T09:00:00+01:00",
    ...overrides,
  };
}

const NAMES = { c1: "Niamh O'Sullivan", c2: "Declan Moore" };

describe("PendingWorkAssembler", () => {
  const assembler = new PendingWorkAssembler();

  it("puts the three origins into a single queue", () => {
    const items = assembler.assemble({
      bookings: [booking()],
      payments: [payment()],
      quotes: [quote()],
      clientNames: NAMES,
    });

    expect(items).toHaveLength(3);
    expect(items.map((item) => item.kind)).toEqual(["BOOKING", "PAYMENT", "QUOTE"]);
  });

  it("shows what has been waiting longest first, whatever its origin", () => {
    const items = assembler.assemble({
      bookings: [booking({ id: "new", requestedAt: "2026-10-09T09:00:00+01:00" })],
      payments: [payment({ id: "oldest", reportedAt: "2026-09-20T09:00:00+01:00" })],
      quotes: [quote({ id: "middle", createdAt: "2026-10-01T09:00:00+01:00" })],
      clientNames: NAMES,
    });

    expect(items.map((item) => item.id)).toEqual(["oldest", "middle", "new"]);
  });

  it("names the client on every origin", () => {
    const items = assembler.assemble({
      bookings: [booking()],
      payments: [payment()],
      quotes: [quote()],
      clientNames: NAMES,
    });

    expect(items.every((item) => item.title === "Niamh O'Sullivan")).toBe(true);
  });

  /** Uma pendência sem rótulo é melhor do que uma pendência escondida: quem não
   * acessa o cadastro de clientes recebe a lista vazia de nomes, e o item
   * precisa continuar aparecendo. */
  it("still shows the item when the client name is unknown", () => {
    const items = assembler.assemble({
      bookings: [booking({ clientId: "missing" })],
      payments: [],
      quotes: [],
      clientNames: {},
    });

    expect(items).toHaveLength(1);
    expect(items[0]?.title).toBe("Client");
  });

  it("shows the amount on a deposit, because it is what gets checked", () => {
    const items = assembler.assemble({
      bookings: [],
      payments: [payment({ amount: "50.00" })],
      quotes: [],
      clientNames: NAMES,
    });

    expect(items[0]?.detail).toContain("€50.00");
    expect(items[0]?.detail).toContain("Deposit");
  });

  /** O critério da etapa é "sem o gestor procurar". Levar à agenda de hoje uma
   * solicitação da semana que vem devolve a procura a ele. */
  it("opens a booking on its own day, not on today", () => {
    const items = assembler.assemble({
      bookings: [booking({ startsAt: "2026-11-20T14:00:00+00:00" })],
      payments: [],
      quotes: [],
      clientNames: NAMES,
    });

    expect(items[0]?.query).toEqual({ day: "2026-11-20" });
  });

  it("opens a deposit on the day of the booking it is holding up", () => {
    const items = assembler.assemble({
      bookings: [booking({ id: "b9", startsAt: "2026-11-20T14:00:00+00:00" })],
      payments: [payment({ bookingId: "b9" })],
      quotes: [],
      clientNames: NAMES,
    });

    const deposit = items.find((item) => item.kind === "PAYMENT");
    expect(deposit?.query).toEqual({ day: "2026-11-20" });
  });

  /** Melhor abrir no dia de hoje do que num dia errado: o sinal de um
   * agendamento que não está na fila não tem data conhecida aqui. */
  it("leaves the day out when the booking is not among the pending ones", () => {
    const items = assembler.assemble({
      bookings: [],
      payments: [payment({ bookingId: "somewhere-else" })],
      quotes: [],
      clientNames: NAMES,
    });

    expect(items[0]?.query).toBeUndefined();
  });

  it("does not send a day to the quotes screen, which has none", () => {
    const items = assembler.assemble({
      bookings: [],
      payments: [],
      quotes: [quote()],
      clientNames: NAMES,
    });

    expect(items[0]?.query).toBeUndefined();
  });

  it("sends each origin to the screen that decides it", () => {
    const items = assembler.assemble({
      bookings: [booking()],
      payments: [payment()],
      quotes: [quote()],
      clientNames: NAMES,
    });

    expect(items.map((item) => item.route)).toEqual(["schedule", "schedule", "quotes"]);
  });

  it("returns nothing when nothing is waiting", () => {
    expect(
      assembler.assemble({ bookings: [], payments: [], quotes: [], clientNames: {} }),
    ).toEqual([]);
  });
});
