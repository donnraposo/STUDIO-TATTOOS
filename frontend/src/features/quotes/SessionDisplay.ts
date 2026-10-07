import type { BadgeTone } from "@/shared/components/StatusBadge.vue";
import type { SessionStatus } from "@/shared/domain/TattooSession";

export interface SessionLook {
  label: string;
  tone: BadgeTone;
}

/** Como uma sessão se apresenta na tela (RN-ORC-005 e RN-ORC-006).
 *
 * **`DONE` é `warning` e não `positive`, e isso é deliberado.** Realizada não é
 * concluída: a sessão ainda espera o gestor confirmar o recebimento, e pintá-la
 * de verde diria ao artista que o trabalho terminou quando ele ainda não entrou
 * em repasse. O verde é de `PAID_OFF`, que é o estado em que o dinheiro conta.
 *
 * Mapa tipado num lugar só, como em `QuoteDisplay` e `PayoutDisplay`.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class SessionDisplay {
  private static readonly STATUS: Record<SessionStatus, SessionLook> = {
    SCHEDULED: { label: "Scheduled", tone: "neutral" },
    DONE: { label: "Performed", tone: "warning" },
    PARTIALLY_DONE: { label: "Partially performed", tone: "warning" },
    PAID_OFF: { label: "Settled", tone: "positive" },
    CANCELLED: { label: "Cancelled", tone: "danger" },
    NO_SHOW: { label: "No-show", tone: "danger" },
  };

  /** Os estados em que o artista ainda pode registrar o que aconteceu.
   *
   * Quitada fica de fora: desfazer uma confirmação de recebimento é ato do
   * gestor, não do artista. */
  private static readonly MARKABLE: SessionStatus[] = ["SCHEDULED", "DONE", "PARTIALLY_DONE"];

  /** Os estados em que o gestor pode confirmar o recebimento. */
  private static readonly CONFIRMABLE: SessionStatus[] = ["DONE", "PARTIALLY_DONE"];

  status(status: SessionStatus): SessionLook {
    return SessionDisplay.STATUS[status];
  }

  canMarkPerformed(status: SessionStatus): boolean {
    return SessionDisplay.MARKABLE.includes(status);
  }

  canConfirmPayment(status: SessionStatus): boolean {
    return SessionDisplay.CONFIRMABLE.includes(status);
  }
}
