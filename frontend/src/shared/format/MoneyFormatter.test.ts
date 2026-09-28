import { describe, expect, it } from "vitest";

import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

describe("MoneyFormatter", () => {
  const money = new MoneyFormatter();

  it("formats the decimal string the API sends", () => {
    expect(money.amount("1000.00")).toBe("€1,000.00");
  });

  it("always shows two decimals, because money is read that way", () => {
    expect(money.amount("50")).toBe("€50.00");
  });

  it("shows a dash instead of NaN when there is no value", () => {
    /** Orçamento pendente tem percentual nulo, e sessão não cobrada tem valor
     * nulo. Mostrar "NaN" faria o usuário achar que o sistema quebrou. */
    expect(money.amount(null)).toBe("—");
    expect(money.amount("")).toBe("—");
    expect(money.amount("abc")).toBe("—");
  });

  it("drops the noise from a whole percentage", () => {
    expect(money.percentage("70.00")).toBe("70%");
    expect(money.percentage("62.50")).toBe("62.5%");
    expect(money.percentage(null)).toBe("—");
  });
});
