import type { PaymentStatus } from "@/shared/domain/Payment";

/** O que ainda se pode fazer com um pagamento (RN-PAG-007).
 *
 * Espelha o `PaymentTransition` do backend: `Informado → Confirmado ou Recusado
 * → Devolvido ou Estornado`. **É aparência, não garantia** — quem recusa a
 * transição é o servidor.
 *
 * **Recusado, devolvido e estornado não vão a lugar nenhum.** Um recusado que
 * voltasse a confirmado apagaria a recusa do histórico, e é isso que a regra
 * proíbe ao mandar corrigir por lançamento de ajuste vinculado. Por isso a
 * tela não oferece botão neles: um botão que o servidor recusa ensina a equipe
 * a desconfiar dos próprios botões.
 *
 * **Estornar não aparece.** O estado existe no backend e não há rota que leve a
 * ele — chega por disputa na operadora, não por decisão de quem opera a tela.
 * Oferecer o botão prometeria uma ação que não existe.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class PaymentTransitions {
  private static readonly ALLOWED: Record<PaymentStatus, PaymentStatus[]> = {
    REPORTED: ["CONFIRMED", "REFUSED"],
    CONFIRMED: ["REFUNDED", "CHARGED_BACK"],
    REFUSED: [],
    REFUNDED: [],
    CHARGED_BACK: [],
  };

  canConfirm(status: PaymentStatus): boolean {
    return PaymentTransitions.ALLOWED[status].includes("CONFIRMED");
  }

  canRefuse(status: PaymentStatus): boolean {
    return PaymentTransitions.ALLOWED[status].includes("REFUSED");
  }

  canRefund(status: PaymentStatus): boolean {
    return PaymentTransitions.ALLOWED[status].includes("REFUNDED");
  }

  /** Nada mais a decidir: o lançamento está encerrado. */
  isFinal(status: PaymentStatus): boolean {
    return PaymentTransitions.ALLOWED[status].length === 0;
  }
}
