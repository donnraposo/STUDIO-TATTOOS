/** Estados do repasse (RN-REP-007).
 *
 * `CALCULATED` é o fechamento feito e ainda não transferido; `PAID` é a
 * transferência confirmada pelo gestor; `ADJUSTED` é o repasse que carrega
 * desconto de uma devolução posterior (RN-REP-005). */
export type PayoutStatus = "CALCULATED" | "PAID" | "ADJUSTED";

/** O repasse de uma semana a um artista (RN-REP-004).
 *
 * **Valores são texto**, como em todo o resto do projeto: a API devolve decimal
 * exato e converter para `number` reintroduziria o arredondamento binário que o
 * `Numeric(12, 2)` do banco existe para evitar. A interface só formata.
 *
 * `periodEnd` é a sexta às 20h `Europe/Dublin` em UTC. A tela formata no fuso do
 * estúdio pelo `StudioClock`, nunca no do navegador — uma semana deslocada por
 * uma hora parece certa, que é o pior tipo de erro. */
export interface Payout {
  id: string;
  artistId: string;
  periodStart: string;
  periodEnd: string;
  grossTotal: string;
  adjustmentsTotal: string;
  netTotal: string;
  status: PayoutStatus;
  paidAt: string | null;
  paidBy: string | null;
}

/** Uma sessão dentro do demonstrativo (RN-REP-007).
 *
 * Os três números que a regra manda exibir — recebido, percentual e o quanto
 * coube ao artista — para que ele refaça a conta sem pedir explicação. */
export interface PayoutItem {
  id: string;
  sessionId: string;
  receivedAmount: string;
  percentage: string;
  amount: string;
}

/** Um desconto de parcela já repassada (RN-REP-005). */
export interface PayoutAdjustment {
  id: string;
  relatedPaymentId: string;
  amount: string;
  reason: string;
  createdAt: string;
}

/** O demonstrativo completo.
 *
 * As três peças vêm juntas porque é assim que se lê: um repasse sem os itens é
 * um número sem explicação, e é a explicação que o artista confere contra o
 * próprio extrato. */
export interface PayoutStatement {
  payout: Payout;
  items: PayoutItem[];
  adjustments: PayoutAdjustment[];
}
