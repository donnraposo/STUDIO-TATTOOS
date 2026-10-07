import { describe, expect, it } from "vitest";

import { RevenueMonth } from "@/features/revenue/RevenueMonth";

/** RN 10.4. O mês corrente vem do fuso do estúdio e não do navegador: um gestor
 * abrindo a tela à meia-noite e meia de 1º de novembro em Dublin, com o
 * navegador noutro fuso, veria outubro e concluiria que o mês não virou.
 */

describe("RevenueMonth", () => {
  const months = new RevenueMonth();

  it("names the month in full for the page title", () => {
    expect(months.label(2026, 10)).toContain("October");
    expect(months.label(2026, 10)).toContain("2026");
  });

  it("names it short for the comparison table", () => {
    expect(months.shortLabel(2026, 10)).toBe("Oct");
    expect(months.shortLabel(2026, 1)).toBe("Jan");
  });

  /** Janeiro para trás é dezembro do ano anterior, e dezembro para frente é
   * janeiro do seguinte. Somar um a um número de mês daria o mês 13. */
  it("crosses the turn of the year in both directions", () => {
    expect(months.previous(2026, 1)).toEqual({ year: 2025, month: 12 });
    expect(months.next(2026, 12)).toEqual({ year: 2027, month: 1 });
  });

  it("walks within the year without touching it", () => {
    expect(months.previous(2026, 10)).toEqual({ year: 2026, month: 9 });
    expect(months.next(2026, 10)).toEqual({ year: 2026, month: 11 });
  });

  /** O teste que mais importa deste arquivo. À meia-noite e meia de 1º de
   * novembro em Dublin já é novembro, mesmo que em UTC ainda seja 31 de
   * outubro — e é o fuso do estúdio que decide o mês do relatório. */
  it("reads the current month in studio time, not in UTC", () => {
    const justAfterMidnightInDublin = new Date("2026-11-01T00:30:00+00:00");

    expect(months.current(justAfterMidnightInDublin)).toEqual({ year: 2026, month: 11 });
  });

  /** O inverso: às 23h30 de 31 de outubro em Dublin ainda é outubro, e no
   * horário de verão irlandês isso já é 22h30 UTC. */
  it("keeps the last night of the month in that month", () => {
    const lastNightInDublin = new Date("2026-10-31T22:30:00+00:00");

    expect(months.current(lastNightInDublin)).toEqual({ year: 2026, month: 10 });
  });

  it("knows which months are still in the future", () => {
    const limit = { year: 2026, month: 10 };

    expect(months.isAfter(2026, 11, limit)).toBe(true);
    expect(months.isAfter(2027, 1, limit)).toBe(true);
    expect(months.isAfter(2026, 10, limit)).toBe(false);
    expect(months.isAfter(2026, 9, limit)).toBe(false);
    expect(months.isAfter(2025, 12, limit)).toBe(false);
  });
});
