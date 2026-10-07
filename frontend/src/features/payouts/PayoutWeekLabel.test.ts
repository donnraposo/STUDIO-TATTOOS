import { describe, expect, it } from "vitest";

import { PayoutWeekLabel } from "@/features/payouts/PayoutWeekLabel";

/** A semana vai de sexta 20h a sexta 20h, no fuso do estúdio (RN-REP-004). A
 * API devolve os dois instantes em UTC, e formatar no fuso do navegador daria
 * uma semana deslocada — que parece certa, e é o pior tipo de erro.
 */

describe("PayoutWeekLabel", () => {
  const label = new PayoutWeekLabel();

  /** Semana de 25 de setembro a 2 de outubro de 2026. Em UTC o fechamento é
   * 19h, porque Dublin está em UTC+1 no verão irlandês. */
  const START = "2026-09-25T19:00:00Z";
  const END = "2026-10-02T19:00:00Z";

  it("names the week by the days it covers", () => {
    const text = label.of(START, END);

    expect(text).toContain("Sept");
    expect(text).toContain("Oct");
  });

  /** A semana **abre** às 20h da sexta anterior, então o primeiro dia inteiro é
   * o sábado. Mostrar a sexta faria o artista procurar nela um atendimento que
   * pertence ao repasse passado. */
  it("starts the label on the day after the opening", () => {
    expect(label.of(START, END)).toContain("26");
  });

  it("shows the closing in studio time, not in UTC", () => {
    /** 19h UTC é 20h em Dublin no verão. Formatado no fuso do navegador, o
     * artista veria a semana fechar às 19h, numa hora que não existe na regra. */
    expect(label.closing(END)).toContain("20:00");
  });

  it("shows the winter closing at the same wall-clock hour", () => {
    /** Em janeiro Dublin está em UTC, e 20h locais são 20h UTC. O mesmo código
     * tem de dar as duas respostas. */
    expect(label.closing("2026-01-09T20:00:00Z")).toContain("20:00");
  });
});
