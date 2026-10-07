import { describe, expect, it } from "vitest";

import { PaymentDisplay } from "@/features/payments/PaymentDisplay";
import type { Payment, PaymentStatus } from "@/shared/domain/Payment";

/** RN-PAG-007 e RN-AGE-009. O que mais importa aqui é a separação entre retido
 * e devolvido: o estúdio ficar com o sinal e o dinheiro sair do caixa são
 * fatos diferentes, e uma tela que mostrasse só o estado contaria a metade
 * errada da história.
 */

function payment(fields: Partial<Payment> = {}): Payment {
  return {
    id: "p1",
    bookingId: "b1",
    sessionId: null,
    clientId: "c1",
    amount: "50.00",
    kind: "DEPOSIT",
    method: "BANK_TRANSFER",
    status: "CONFIRMED",
    note: null,
    reportedAt: "2026-10-01T10:00:00Z",
    confirmedAt: "2026-10-01T11:00:00Z",
    refusedAt: null,
    refusalReason: null,
    retainedAt: null,
    retainedReason: null,
    ...fields,
  };
}

describe("PaymentDisplay", () => {
  const display = new PaymentDisplay();

  it("names every payment state", () => {
    const named: PaymentStatus[] = [
      "REPORTED",
      "CONFIRMED",
      "REFUSED",
      "REFUNDED",
      "CHARGED_BACK",
    ];

    for (const status of named) {
      expect(display.status(status).label).not.toBe("");
    }
  });

  /** Um recebimento informado e não conferido é a única coisa desta tela que
   * trava outra: sem ele o horário não pode ser aprovado (RN-AGE-005). Cinza o
   * deixaria no mesmo peso de um histórico encerrado. */
  it("puts an unconfirmed receipt in a waiting tone, not a neutral one", () => {
    expect(display.status("REPORTED").tone).toBe("warning");
    expect(display.status("CONFIRMED").tone).toBe("positive");
  });

  /** Devolver é o desfecho correto quando o estúdio recusa a solicitação
   * (RN-PAG-003). Vermelho ali ensinaria a equipe a tratar o certo como erro —
   * e aí o vermelho da recusa, que é um comprovante que não valeu, deixaria de
   * significar alguma coisa. */
  it("separates a refund, which is correct, from a refusal, which is not", () => {
    expect(display.status("REFUNDED").tone).toBe("neutral");
    expect(display.status("REFUSED").tone).toBe("danger");
  });

  it("names the kinds and methods in plain English", () => {
    expect(display.kind("DEPOSIT")).toBe("Deposit");
    expect(display.kind("FULL_PREPAY")).toBe("Full prepayment");
    expect(display.method("BANK_TRANSFER")).toBe("Bank transfer");
    expect(display.method("CASH")).toBe("Cash");
  });

  /** O teste que mais importa deste arquivo. O sinal retido continua
   * confirmado: o horário foi reservado e perdido, e a RN-AGE-009 manda o
   * estúdio ficar com ele. Quem lesse apenas "Confirmed" procuraria a
   * devolução que nunca houve. */
  it("shows that the studio kept a deposit, which is not the same as refunded", () => {
    const kept = payment({ retainedAt: "2026-10-02T09:00:00Z", status: "CONFIRMED" });

    expect(display.isRetained(kept)).toBe(true);
    expect(display.status(kept.status).label).toBe("Confirmed");
  });

  it("does not call an ordinary confirmed payment retained", () => {
    expect(display.isRetained(payment())).toBe(false);
  });
});
