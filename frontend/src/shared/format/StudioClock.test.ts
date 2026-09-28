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
});
