import { HttpClient } from "@/shared/api/HttpClient";
import type {
  Payment,
  PaymentKind,
  PaymentMethod,
  PaymentRefund,
  PaymentStatus,
} from "@/shared/domain/Payment";

interface PaymentPayload {
  id: string;
  booking_id: string | null;
  session_id: string | null;
  client_id: string | null;
  amount: string;
  kind: string;
  method: string;
  status: string;
  note: string | null;
  reported_at: string;
  confirmed_at: string | null;
  refused_at: string | null;
  refusal_reason: string | null;
  retained_at: string | null;
  retained_reason: string | null;
}

interface RefundPayload {
  id: string;
  payment_id: string;
  amount: string;
  method: string;
  reason: string;
  note: string | null;
  refunded_at: string;
}

/** Pagamentos e sinal (`/payments`).
 *
 * **Confirmar, recusar e devolver são ações próprias**, e não um campo que se
 * edita. Cada uma registra coisas diferentes, e a RN-PAG-007 proíbe o caminho
 * que um `PATCH` de estado abriria: voltar um recusado a confirmado, apagando a
 * recusa do histórico.
 *
 * Não há método de exclusão porque não há rota: um pagamento nunca é apagado. */
export class PaymentsClient {
  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  /** Os pagamentos do estúdio aguardando confirmação (seção 10.1).
   *
   * Só o gestor consegue — quem confirma recebimento é ele (RN-PAG-002), e o
   * backend recusa os demais com 403. Desde a M5 o sinal não confirmado trava a
   * aprovação do horário, então esta fila é a mesma dor das solicitações
   * esquecidas, por outro caminho. */
  async listAwaitingConfirmation(): Promise<Payment[]> {
    return this.listByStatus("REPORTED");
  }

  /** Os pagamentos num estado qualquer, para o gestor percorrer o histórico.
   *
   * O estado vai na consulta e não é filtrado aqui: a lista inteira do estúdio
   * no navegador para peneirar seria trazer seis anos de registro financeiro
   * (RN-CLI-007) a cada abertura da tela. */
  async listByStatus(status: PaymentStatus): Promise<Payment[]> {
    const payload = await this.http.get<PaymentPayload[]>(`/payments?status=${status}`);
    return payload.map(PaymentsClient.toPayment);
  }

  async listForBooking(bookingId: string): Promise<Payment[]> {
    const payload = await this.http.get<PaymentPayload[]>(`/bookings/${bookingId}/payments`);
    return payload.map(PaymentsClient.toPayment);
  }

  async register(payment: {
    bookingId: string | null;
    sessionId: string | null;
    clientId: string | null;
    amount: string;
    kind: PaymentKind;
    method: PaymentMethod;
    note: string | null;
  }): Promise<Payment> {
    return PaymentsClient.toPayment(
      await this.http.post<PaymentPayload>("/payments", {
        booking_id: payment.bookingId,
        session_id: payment.sessionId,
        client_id: payment.clientId,
        amount: payment.amount,
        kind: payment.kind,
        method: payment.method,
        note: payment.note,
      }),
    );
  }

  async confirm(paymentId: string): Promise<Payment> {
    return PaymentsClient.toPayment(
      await this.http.post<PaymentPayload>(`/payments/${paymentId}/confirm`),
    );
  }

  async refuse(paymentId: string, reason: string): Promise<Payment> {
    return PaymentsClient.toPayment(
      await this.http.post<PaymentPayload>(`/payments/${paymentId}/refuse`, { reason }),
    );
  }

  /** Registra uma devolução **já realizada** (RN-PAG-009).
   *
   * O sistema não movimenta dinheiro nesta versão: o gestor devolve por fora e
   * lança aqui. O valor é texto do campo ao corpo da requisição, sem passar por
   * `number`. */
  async refund(
    paymentId: string,
    refund: { amount: string; method: PaymentMethod; reason: string; note: string | null },
  ): Promise<PaymentRefund> {
    const payload = await this.http.post<RefundPayload>(`/payments/${paymentId}/refund`, {
      amount: refund.amount,
      method: refund.method,
      reason: refund.reason,
      note: refund.note,
    });
    return {
      id: payload.id,
      paymentId: payload.payment_id,
      amount: payload.amount,
      method: payload.method as PaymentMethod,
      reason: payload.reason,
      note: payload.note,
      refundedAt: payload.refunded_at,
    };
  }

  private static toPayment(payload: PaymentPayload): Payment {
    return {
      id: payload.id,
      bookingId: payload.booking_id,
      sessionId: payload.session_id,
      clientId: payload.client_id,
      amount: payload.amount,
      kind: payload.kind as PaymentKind,
      method: payload.method as PaymentMethod,
      status: payload.status as PaymentStatus,
      note: payload.note,
      reportedAt: payload.reported_at,
      confirmedAt: payload.confirmed_at,
      refusedAt: payload.refused_at,
      refusalReason: payload.refusal_reason,
      retainedAt: payload.retained_at,
      retainedReason: payload.retained_reason,
    };
  }
}
