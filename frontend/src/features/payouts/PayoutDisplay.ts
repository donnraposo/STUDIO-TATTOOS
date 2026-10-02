import type { BadgeTone } from "@/shared/components/StatusBadge.vue";
import type { PayoutStatus } from "@/shared/domain/Payout";

export interface PayoutLook {
  label: string;
  tone: BadgeTone;
}

/** Como um repasse se apresenta na tela (RN-REP-007).
 *
 * Mapa tipado num lugar só, como em `QuoteDisplay`. A lista e o demonstrativo
 * mostram o mesmo estado; se cada um trouxesse o próprio mapa, bastaria
 * acrescentar um estado para que um deles passasse a exibir o nome cru da API.
 *
 * **`PAID` é positivo e `CALCULATED` é neutro, não de alerta.** Um fechamento
 * calculado e ainda não transferido não é problema — é o estado normal entre a
 * sexta e o momento em que o gestor faz a transferência. Pintá-lo de alerta
 * ensinaria a equipe a ignorar o alerta.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class PayoutDisplay {
  private static readonly STATUS: Record<PayoutStatus, PayoutLook> = {
    CALCULATED: { label: "Calculated", tone: "neutral" },
    PAID: { label: "Paid", tone: "positive" },
    ADJUSTED: { label: "Adjusted", tone: "info" },
  };

  status(status: PayoutStatus): PayoutLook {
    return PayoutDisplay.STATUS[status];
  }
}
