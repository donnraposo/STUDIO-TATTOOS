import { describe, expect, it } from "vitest";

import { StudioClock } from "@/shared/format/StudioClock";

/** O que estes testes protegem é o erro que não se percebe olhando: uma agenda
 * deslocada por uma hora parece perfeitamente correta na tela. */
describe("StudioClock", () => {
  const clock = new StudioClock();

  it("shows the studio time, not the browser time", () => {
    // 10:00 em Dublin no horário de verão irlandês é 09:00 UTC.
    expect(clock.time("2026-07-15T09:00:00+00:00")).toBe("10:00");
  });

  it("shows the studio time in winter, when the offset is zero", () => {
    expect(clock.time("2026-01-15T09:00:00+00:00")).toBe("09:00");
  });

  it("keeps the same wall-clock reading whatever offset the API sends", () => {
    /** O mesmo instante, escrito de duas formas. A tela precisa mostrar o
     * mesmo horário nas duas, senão o deslocamento do servidor vaza para o
     * usuário. */
    expect(clock.time("2026-07-15T09:00:00+00:00")).toBe(clock.time("2026-07-15T10:00:00+01:00"));
  });

  it("counts minutes from midnight in the studio, across daylight saving", () => {
    const summer = clock.minutesSinceMidnight("2026-07-15T09:00:00+00:00");
    const winter = clock.minutesSinceMidnight("2026-01-15T09:00:00+00:00");

    expect(summer).toBe(600);
    expect(winter).toBe(540);
  });

  it("formats a date the way the studio reads it", () => {
    expect(clock.date("2026-10-06T10:00:00+01:00")).toContain("Oct");
  });

  it("gives the day key a date field understands", () => {
    expect(clock.dayKey("2026-10-06T10:00:00+01:00")).toBe("2026-10-06");
  });

  it("keeps a late booking on the studio's day, not on UTC's", () => {
    /** 00h30 de terça em Dublin, no horário de verão, ainda é segunda em UTC.
     * `toISOString().slice(0, 10)` colocaria essa reserva no dia anterior — uma
     * hora de largura, só de madrugada e só em parte do ano, que é o tipo de
     * defeito que ninguém reproduz quando é relatado. */
    const lateBooking = "2026-07-14T00:30:00+01:00";

    expect(new Date(lateBooking).toISOString().slice(0, 10)).toBe("2026-07-13");
    expect(clock.dayKey(lateBooking)).toBe("2026-07-14");
  });

  it("reads today by the same ruler", () => {
    expect(clock.today(new Date("2026-07-14T00:30:00+01:00"))).toBe("2026-07-14");
  });
});
