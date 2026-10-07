import { describe, expect, it } from "vitest";

import { SessionDisplay } from "@/features/quotes/SessionDisplay";

/** RN-ORC-005 e RN-ORC-006. O que importa aqui é a separação entre realizada e
 * concluída: a primeira ainda não entra em repasse, e a tela não pode sugerir
 * que entra.
 */

describe("SessionDisplay", () => {
  const display = new SessionDisplay();

  it("names every session state in plain English", () => {
    expect(display.status("SCHEDULED").label).toBe("Scheduled");
    expect(display.status("DONE").label).toBe("Performed");
    expect(display.status("PARTIALLY_DONE").label).toBe("Partially performed");
    expect(display.status("PAID_OFF").label).toBe("Settled");
  });

  /** Realizada não é concluída: a sessão ainda espera o gestor confirmar o
   * recebimento. Verde diria ao artista que o trabalho terminou quando ele
   * ainda não conta para o fechamento de sexta. */
  it("keeps performed in a waiting tone, and settled in a positive one", () => {
    expect(display.status("DONE").tone).toBe("warning");
    expect(display.status("PARTIALLY_DONE").tone).toBe("warning");
    expect(display.status("PAID_OFF").tone).toBe("positive");
  });

  it("lets the artist record and correct what happened", () => {
    expect(display.canMarkPerformed("SCHEDULED")).toBe(true);
    expect(display.canMarkPerformed("DONE")).toBe(true);
    expect(display.canMarkPerformed("PARTIALLY_DONE")).toBe(true);
  });

  /** Desfazer uma confirmação de recebimento é ato do gestor, não do artista. */
  it("stops the artist from re-marking a settled session", () => {
    expect(display.canMarkPerformed("PAID_OFF")).toBe(false);
  });

  it("only offers confirmation on a session that happened", () => {
    expect(display.canConfirmPayment("SCHEDULED")).toBe(false);
    expect(display.canConfirmPayment("DONE")).toBe(true);
    expect(display.canConfirmPayment("PARTIALLY_DONE")).toBe(true);
    expect(display.canConfirmPayment("PAID_OFF")).toBe(false);
  });
});
