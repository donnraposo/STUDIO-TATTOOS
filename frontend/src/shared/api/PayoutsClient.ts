import { HttpClient } from "@/shared/api/HttpClient";
import type {
  Payout,
  PayoutAdjustment,
  PayoutItem,
  PayoutStatement,
  PayoutStatus,
} from "@/shared/domain/Payout";

interface PayoutPayload {
  id: string;
  artist_id: string;
  period_start: string;
  period_end: string;
  gross_total: string;
  adjustments_total: string;
  net_total: string;
  status: string;
  paid_at: string | null;
  paid_by: string | null;
}

interface ItemPayload {
  id: string;
  session_id: string;
  received_amount: string;
  percentage: string;
  amount: string;
}

interface AdjustmentPayload {
  id: string;
  related_payment_id: string;
  amount: string;
  reason: string;
  created_at: string;
}

interface StatementPayload {
  payout: PayoutPayload;
  items: ItemPayload[];
  adjustments: AdjustmentPayload[];
}

/** Repasses semanais (`/payouts`).
 *
 * **O recorte é do servidor** (RN-REP-004): o artista recebe só os próprios
 * repasses, o gestor recebe todos. A tela não filtra — filtrar aqui daria duas
 * versões da regra, e a do navegador seria a que silenciosamente ficaria para
 * trás. Num módulo que diz quanto cada pessoa recebeu, essa divergência é a
 * última que se quer.
 *
 * Não há método de recálculo nem de exclusão porque não há rota: um repasse é
 * fotografia da semana, e correção entra como ajuste negativo no seguinte. */
export class PayoutsClient {
  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  async list(): Promise<Payout[]> {
    const payload = await this.http.get<PayoutPayload[]>("/payouts");
    return payload.map(PayoutsClient.toPayout);
  }

  /** Fecha a semana que contém `reference` e devolve os repasses dela.
   *
   * **Idempotente:** fechar duas vezes devolve o mesmo fechamento. O instante é
   * qualquer um dentro da semana desejada, e não a data da sexta — quem calcula
   * as 20h no fuso do estúdio é o servidor, e errar essa conta por uma hora move
   * pagamentos de uma semana para a outra. */
  async closeWeek(reference: string): Promise<Payout[]> {
    const payload = await this.http.post<PayoutPayload[]>("/payouts/close", {
      reference,
    });
    return payload.map(PayoutsClient.toPayout);
  }

  async statement(payoutId: string): Promise<PayoutStatement> {
    const payload = await this.http.get<StatementPayload>(`/payouts/${payoutId}`);
    return {
      payout: PayoutsClient.toPayout(payload.payout),
      items: payload.items.map(PayoutsClient.toItem),
      adjustments: payload.adjustments.map(PayoutsClient.toAdjustment),
    };
  }

  /** Registra que o gestor transferiu. **Não transfere** — o sistema nunca move
   * dinheiro sozinho (RN-REP-004). */
  async confirmPaid(payoutId: string): Promise<Payout> {
    return PayoutsClient.toPayout(
      await this.http.post<PayoutPayload>(`/payouts/${payoutId}/confirm-paid`, {
        receipt_object_key: null,
      }),
    );
  }

  private static toPayout(payload: PayoutPayload): Payout {
    return {
      id: payload.id,
      artistId: payload.artist_id,
      periodStart: payload.period_start,
      periodEnd: payload.period_end,
      grossTotal: payload.gross_total,
      adjustmentsTotal: payload.adjustments_total,
      netTotal: payload.net_total,
      status: payload.status as PayoutStatus,
      paidAt: payload.paid_at,
      paidBy: payload.paid_by,
    };
  }

  private static toItem(payload: ItemPayload): PayoutItem {
    return {
      id: payload.id,
      sessionId: payload.session_id,
      receivedAmount: payload.received_amount,
      percentage: payload.percentage,
      amount: payload.amount,
    };
  }

  private static toAdjustment(payload: AdjustmentPayload): PayoutAdjustment {
    return {
      id: payload.id,
      relatedPaymentId: payload.related_payment_id,
      amount: payload.amount,
      reason: payload.reason,
      createdAt: payload.created_at,
    };
  }
}
