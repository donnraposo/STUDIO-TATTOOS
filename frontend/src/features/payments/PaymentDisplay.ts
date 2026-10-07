import type { BadgeTone } from "@/shared/components/StatusBadge.vue";
import type {
  Payment,
  PaymentKind,
  PaymentMethod,
  PaymentStatus,
} from "@/shared/domain/Payment";

export interface PaymentLook {
  label: string;
  tone: BadgeTone;
}

/** Como um pagamento se apresenta na tela (RN-PAG-007).
 *
 * Mapas tipados num lugar só, como em `PayoutDisplay`. A fila do painel, a tela
 * de pagamentos e o sinal dentro do agendamento falam dos mesmos estados; cada
 * um com o seu mapa passaria a exibir `CHARGED_BACK` cru no primeiro estado
 * novo.
 *
 * **`REPORTED` é alerta e não neutro.** Um recebimento informado e ainda não
 * conferido é a única coisa desta tela que trava outra: sem a confirmação, o
 * horário não pode ser aprovado (RN-AGE-005). Pintá-lo de cinza o deixaria no
 * mesmo peso visual de um histórico encerrado.
 *
 * **`REFUNDED` é neutro e não perigo.** Devolver não é defeito — é o desfecho
 * correto quando o estúdio recusa a solicitação (RN-PAG-003). Vermelho ali
 * ensinaria a equipe a tratar o certo como erro. Quem é perigo é `REFUSED`: um
 * comprovante que não valeu.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class PaymentDisplay {
  private static readonly STATUS: Record<PaymentStatus, PaymentLook> = {
    REPORTED: { label: "Awaiting confirmation", tone: "warning" },
    CONFIRMED: { label: "Confirmed", tone: "positive" },
    REFUSED: { label: "Refused", tone: "danger" },
    REFUNDED: { label: "Refunded", tone: "neutral" },
    CHARGED_BACK: { label: "Charged back", tone: "danger" },
  };

  private static readonly KIND: Record<PaymentKind, string> = {
    DEPOSIT: "Deposit",
    BALANCE: "Balance",
    FULL_PREPAY: "Full prepayment",
    GUEST_WEEK: "Guest week",
  };

  private static readonly METHOD: Record<PaymentMethod, string> = {
    BANK_TRANSFER: "Bank transfer",
    CASH: "Cash",
    CARD: "Card",
  };

  status(status: PaymentStatus): PaymentLook {
    return PaymentDisplay.STATUS[status];
  }

  kind(kind: PaymentKind): string {
    return PaymentDisplay.KIND[kind];
  }

  method(method: PaymentMethod): string {
    return PaymentDisplay.METHOD[method];
  }

  /** O estúdio ficou com o sinal, e isso **não** é o mesmo que devolvido.
   *
   * Um sinal retido continua `CONFIRMED` — o horário foi reservado e perdido, e
   * a RN-AGE-009 manda o estúdio ficar com ele. Uma tela que mostrasse só o
   * estado contaria a metade errada da história: o gestor veria "Confirmed" e
   * procuraria a devolução que nunca houve. */
  isRetained(payment: Payment): boolean {
    return payment.retainedAt !== null;
  }
}
