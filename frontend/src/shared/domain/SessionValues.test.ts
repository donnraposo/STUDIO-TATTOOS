import { describe, expect, it } from "vitest";

import { SessionValues } from "@/shared/domain/SessionValues";

/** RN-ORC-004 e RN-PAG-001. O valor total e o valor por sessão são o mesmo fato
 * dito de duas formas, e pedir os dois ao tatuador abriria a chance de eles
 * discordarem — o repasse sairia de um e o orçamento aprovado do outro.
 */

describe("SessionValues", () => {
  const values = new SessionValues();

  it("multiplies the session value into the total", () => {
    expect(values.totalFrom("250.00", 4)).toBe("1000.00");
    expect(values.totalFrom("80", 1)).toBe("80.00");
  });

  it("divides the total across the sessions", () => {
    expect(values.perSessionFrom("1000.00", 4)).toBe("250.00");
  });

  /** O teste que mais importa deste arquivo. A RN-PAG-001 diz que a soma dos
   * sinais e saldos das sessões não pode ultrapassar o valor total aprovado.
   * €1.000 em três: €333,34 somaria €1.000,02 e estouraria o teto. */
  it("rounds down so the sessions never add up past the total", () => {
    const perSession = values.perSessionFrom("1000.00", 3);

    expect(perSession).toBe("333.33");
    expect(Number(perSession) * 3).toBeLessThanOrEqual(1000);
  });

  /** Centavos inteiros, e não ponto flutuante: `0.1 + 0.2` não dá `0.3` em
   * binário, e aqui o resultado vira o que alguém recebe. */
  it("survives the values that break floating point", () => {
    expect(values.totalFrom("0.10", 3)).toBe("0.30");
    expect(values.totalFrom("33.33", 3)).toBe("99.99");
  });

  /** Um campo que se preenche sozinho com `NaN` enquanto alguém digita parece
   * defeito do sistema. */
  it("fills nothing from an empty or broken field", () => {
    expect(values.totalFrom("", 4)).toBe("");
    expect(values.perSessionFrom("abc", 4)).toBe("");
    expect(values.perSessionFrom("1000", 0)).toBe("");
  });

  /** Basta um dos dois: é o ponto inteiro da mudança. */
  it("accepts either side as enough to quote", () => {
    expect(values.isComplete("1000.00", "")).toBe(true);
    expect(values.isComplete("", "250.00")).toBe(true);
  });

  it("refuses when neither side has a value", () => {
    expect(values.isComplete("", "")).toBe(false);
    expect(values.isComplete("0", "0")).toBe(false);
    expect(values.isComplete("abc", "")).toBe(false);
  });
});
