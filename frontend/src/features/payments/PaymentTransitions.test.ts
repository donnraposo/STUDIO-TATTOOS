import { describe, expect, it } from "vitest";

import { PaymentTransitions } from "@/features/payments/PaymentTransitions";
import type { PaymentStatus } from "@/shared/domain/Payment";

/** RN-PAG-007: `Informado → Confirmado ou Recusado → Devolvido ou Estornado`.
 *
 * O que mais importa aqui é o que **não** se pode fazer. Um pagamento recusado
 * que voltasse a confirmado apagaria a recusa do histórico, e é exatamente isso
 * que a regra proíbe ao mandar corrigir por lançamento de ajuste vinculado.
 */

describe("PaymentTransitions", () => {
  const transitions = new PaymentTransitions();

  it("offers confirm and refuse on a payment that was only reported", () => {
    expect(transitions.canConfirm("REPORTED")).toBe(true);
    expect(transitions.canRefuse("REPORTED")).toBe(true);
  });

  /** Devolver o que ainda não foi conferido seria devolver dinheiro que o
   * estúdio não sabe se recebeu. */
  it("does not offer a refund before the receipt is confirmed", () => {
    expect(transitions.canRefund("REPORTED")).toBe(false);
  });

  it("offers only the refund once the receipt is confirmed", () => {
    expect(transitions.canRefund("CONFIRMED")).toBe(true);
    expect(transitions.canConfirm("CONFIRMED")).toBe(false);
    expect(transitions.canRefuse("CONFIRMED")).toBe(false);
  });

  /** O teste que mais importa deste arquivo. */
  it("never lets a refused payment come back", () => {
    expect(transitions.canConfirm("REFUSED")).toBe(false);
    expect(transitions.canRefuse("REFUSED")).toBe(false);
    expect(transitions.canRefund("REFUSED")).toBe(false);
  });

  it("closes a payment that was refunded or charged back", () => {
    const closed: PaymentStatus[] = ["REFUSED", "REFUNDED", "CHARGED_BACK"];

    for (const status of closed) {
      expect(transitions.isFinal(status)).toBe(true);
    }
  });

  it("keeps the two live states open", () => {
    expect(transitions.isFinal("REPORTED")).toBe(false);
    expect(transitions.isFinal("CONFIRMED")).toBe(false);
  });
});
