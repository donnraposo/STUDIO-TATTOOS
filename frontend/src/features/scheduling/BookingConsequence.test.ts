import { describe, expect, it } from "vitest";

import {
  BookingConsequence,
  type BookingDecisionKind,
} from "@/features/scheduling/BookingConsequence";

/** RN-AGE-008, RN-AGE-009, RN-PAG-003 e RN-PAG-004.
 *
 * **Este arquivo existe por um texto que apodreceu.** A frase da aprovação
 * dizia que o sinal não era registrado no sistema e mandava confirmá-lo por
 * fora — verdade até a M7.2.3, e falsa a partir dela, quando o painel do sinal
 * passou a ficar no mesmo modal, logo acima dela. Um texto que contradiz o que
 * está na tela ao lado é pior do que texto nenhum: ensina a não ler nenhum dos
 * dois.
 *
 * O que se prende aqui não é a redação, e sim o fato que cada frase precisa
 * carregar — e, no caso da aprovação, o que ela não pode mais afirmar.
 */

describe("BookingConsequence", () => {
  const consequences = new BookingConsequence();

  it("has something to say about every decision", () => {
    const decisions: BookingDecisionKind[] = [
      "approve",
      "reject",
      "cancel",
      "noShow",
      "reschedule",
    ];

    for (const decision of decisions) {
      expect(consequences.describe(decision).length).toBeGreaterThan(0);
    }
  });

  /** O teste que motivou o arquivo. */
  it("no longer claims the deposit lives outside the system", () => {
    const text = consequences.describe("approve").toLowerCase();

    expect(text).not.toContain("outside the system");
    expect(text).not.toContain("not recorded");
  });

  it("still says the deposit has to be confirmed before approving", () => {
    expect(consequences.describe("approve").toLowerCase()).toContain("confirmed");
  });

  /** RN-PAG-003: quando é o estúdio que recusa, o sinal volta inteiro. */
  it("says the studio returns the deposit when it is the studio that refuses", () => {
    expect(consequences.describe("reject").toLowerCase()).toContain("return");
  });

  /** RN-AGE-009: o estúdio fica com o sinal mesmo com aviso de 24 horas. Omitir
   * isso faria o gestor cancelar achando que devolve. */
  it("warns that cancelling keeps the deposit even with notice", () => {
    const text = consequences.describe("cancel").toLowerCase();

    expect(text).toContain("keeps the deposit");
    expect(text).toContain("24 hours");
  });

  /** **Deixou de dizer um valor em 08/10/2026.** Cada artista cobra o seu
   * sinal, e prometer cinquenta euros a quem combinou oitenta erra justamente
   * onde dói: no que o cliente recebe de volta. */
  it("names no fixed amount, because the deposit varies by artist", () => {
    const decisions: BookingDecisionKind[] = ["approve", "cancel", "noShow", "reschedule"];

    for (const decision of decisions) {
      expect(consequences.describe(decision)).not.toContain("€50");
    }
  });

  /** O não comparecimento tira também o repasse do artista, e é o que o
   * distingue de um cancelamento. */
  it("says a no-show costs the artist the payout as well", () => {
    expect(consequences.describe("noShow").toLowerCase()).toContain("payout");
  });

  /** RN-AGE-008: dentro das 24 horas o sinal acompanha o horário; fora delas o
   * cliente paga um novo. */
  it("separates the two sides of the rescheduling deadline", () => {
    const text = consequences.describe("reschedule").toLowerCase();

    expect(text).toContain("24 hours");
    expect(text).toContain("new deposit");
  });
});
