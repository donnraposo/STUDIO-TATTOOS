import { describe, expect, it } from "vitest";

import { RevenueBars } from "@/features/revenue/RevenueBars";
import type { MonthlyRevenue } from "@/shared/domain/Revenue";

/** A proporção das barras da comparação entre meses.
 *
 * É geometria, e é onde um erro passa despercebido: uma barra com a proporção
 * errada não quebra nada, só mente — e quem olha um gráfico não confere a conta.
 */

function month(value: string, year = 2026, monthNumber = 10): MonthlyRevenue {
  return {
    year,
    month: monthNumber,
    totals: { sessions: 1, value, artists: "0.00", studio: "0.00" },
  };
}

describe("RevenueBars", () => {
  const bars = new RevenueBars();

  /** A escala é relativa ao maior mês do período, e não a um teto fixo: o
   * estúdio compara meses entre si, e um eixo absoluto faria todos parecerem
   * iguais num ano fraco. */
  it("gives the best month the full width", () => {
    const widths = bars.heights([month("500.00"), month("1000.00")]);

    expect(widths[1]).toBe(100);
    expect(widths[0]).toBe(50);
  });

  /** Sumir com o mês vazio faria a comparação mentir sobre o tempo: um mês
   * zerado ao lado de um mês cheio é informação. */
  it("keeps an empty month at zero instead of dropping it", () => {
    const widths = bars.heights([month("0.00"), month("800.00")]);

    expect(widths).toHaveLength(2);
    expect(widths[0]).toBe(0);
  });

  /** Dividir por zero daria `NaN`, e uma largura `NaN%` é uma barra que o
   * navegador desenha como lixo ou não desenha. */
  it("survives a period where nothing was tattooed", () => {
    expect(bars.heights([month("0.00"), month("0.00")])).toEqual([0, 0]);
  });

  it("has nothing to draw for an empty period", () => {
    expect(bars.heights([])).toEqual([]);
  });

  it("finds the month that earned the most", () => {
    const best = bars.best([
      month("500.00", 2026, 8),
      month("1200.00", 2026, 9),
      month("900.00", 2026, 10),
    ]);

    expect(best?.month).toBe(9);
  });

  /** Destacar um zero entre zeros não diz nada a ninguém. */
  it("picks no best month when nothing was earned", () => {
    expect(bars.best([month("0.00"), month("0.00")])).toBeNull();
    expect(bars.best([])).toBeNull();
  });
});
