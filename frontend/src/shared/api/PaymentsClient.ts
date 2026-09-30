import { HttpClient } from "@/shared/api/HttpClient";
import type {
  Payment,
  PaymentKind,
  PaymentMethod,
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
    const payload = await this.http.get<PaymentPayload[]>("/payments?status=REPORTED");
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
