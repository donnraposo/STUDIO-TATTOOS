import { describe, expect, it } from "vitest";

import { ArtistBoard } from "@/features/home/ArtistBoard";
import type { Booking } from "@/shared/domain/Booking";
import type { Payout } from "@/shared/domain/Payout";
import type { Quote } from "@/shared/domain/Quote";

/** Seções 10.2 e 10.3. O que mais importa aqui é o que a classe **não** faz:
 * não filtra por artista, porque o recorte é do backend, e não prevê repasse,
 * porque o repasse só existe depois do fechamento de sexta (RN-REP-004).
 */

function booking(fields: Partial<Booking> = {}): Booking {
  return {
    id: "b1",
    clientId: "c1",
    artistId: "a1",
    benchId: "bench1",
    startsAt: "2026-10-06T10:00:00Z",
    endsAt: "2026-10-06T12:00:00Z",
    status: "APPROVED",
    requestedAt: "2026-10-05T09:00:00Z",
    rejectionReason: null,
    rejectionNote: null,
    ...fields,
  };
}

function payout(fields: Partial<Payout> = {}): Payout {
  return {
    id: "p1",
    artistId: "a1",
    periodStart: "2026-09-25T19:00:00Z",
    periodEnd: "2026-10-02T19:00:00Z",
    grossTotal: "500.00",
    adjustmentsTotal: "0.00",
    netTotal: "350.00",
    status: "CALCULATED",
    paidAt: null,
    paidBy: null,
    ...fields,
  };
}

function quote(status: Quote["status"]): Quote {
  return { id: `q-${status}`, status } as Quote;
}

describe("ArtistBoard", () => {
  const board = new ArtistBoard();

  it("puts the day in the order it will happen", () => {
    const day = board.today([
      booking({ id: "late", startsAt: "2026-10-06T16:00:00Z" }),
      booking({ id: "early", startsAt: "2026-10-06T09:00:00Z" }),
    ]);

    expect(day.map((item) => item.id)).toEqual(["early", "late"]);
  });

  /** Um horário recusado na lista do dia faria o artista procurar um cliente
   * que não vem. */
  it("leaves cancelled and rejected out of the day", () => {
    const day = board.today([
      booking({ id: "live" }),
      booking({ id: "gone", status: "REJECTED" }),
      booking({ id: "off", status: "CANCELLED" }),
    ]);

    expect(day.map((item) => item.id)).toEqual(["live"]);
  });

  /** A solicitação ainda não decidida continua no dia: ela pode ser aprovada a
   * qualquer momento, e escondê-la faria o artista chegar sem saber. */
  it("keeps a request that is still waiting for the studio", () => {
    expect(board.today([booking({ status: "REQUESTED" })])).toHaveLength(1);
  });

  it("finds what comes next, and ignores what already ended", () => {
    const bookings = [
      booking({ id: "done", startsAt: "2026-10-06T09:00:00Z", endsAt: "2026-10-06T10:00:00Z" }),
      booking({ id: "next", startsAt: "2026-10-06T14:00:00Z", endsAt: "2026-10-06T16:00:00Z" }),
    ];

    expect(board.next(bookings, "2026-10-06T11:00:00Z")?.id).toBe("next");
  });

  /** Durante o atendimento, o próximo é o que está em curso — não o seguinte.
   * Mostrar o seguinte às 11h faria o artista achar que a maca está livre. */
  it("counts the booking in progress as the current one", () => {
    const bookings = [
      booking({ id: "running", startsAt: "2026-10-06T10:00:00Z", endsAt: "2026-10-06T12:00:00Z" }),
    ];

    expect(board.next(bookings, "2026-10-06T11:00:00Z")?.id).toBe("running");
  });

  it("has nothing next once the day is over", () => {
    expect(board.next([booking()], "2026-10-06T23:00:00Z")).toBeNull();
  });

  it("counts what the studio has not decided yet", () => {
    const bookings = [
      booking({ status: "REQUESTED" }),
      booking({ status: "REQUESTED" }),
      booking({ status: "APPROVED" }),
    ];

    expect(board.awaitingDecision(bookings)).toBe(2);
  });

  it("counts only the quotes still pending", () => {
    expect(board.quotesPending([quote("PENDING"), quote("APPROVED"), quote("PENDING")])).toBe(2);
  });

  /** O teste que mais importa deste arquivo. O repasse mais recente é o do
   * último fechamento, e não há previsão da semana corrente: um número
   * calculado no navegador seria o sistema dizendo ao artista quanto ele vai
   * receber sem que ninguém tenha fechado nada (RN-REP-004). */
  it("shows the most recent closing, never a forecast", () => {
    const last = board.lastPayout([
      payout({ id: "older", periodEnd: "2026-09-25T19:00:00Z" }),
      payout({ id: "newest", periodEnd: "2026-10-02T19:00:00Z" }),
    ]);

    expect(last?.id).toBe("newest");
  });

  it("has no payout to show before the first closing", () => {
    expect(board.lastPayout([])).toBeNull();
  });
});
