/** O que o pagamento cobre (RN-PAG-001, RN-PAG-004 e RN-GST-001). */
export type PaymentKind = "DEPOSIT" | "BALANCE" | "FULL_PREPAY" | "GUEST_WEEK";

/** Como o dinheiro entrou ou saiu (RN-PAG-002 e RN-PAG-006). */
export type PaymentMethod = "BANK_TRANSFER" | "CASH" | "CARD";

/** Estados do pagamento (RN-PAG-007).
 *
 * `Informado → Confirmado ou Recusado → Devolvido ou Estornado`. Nenhum deles
 * apaga o lançamento: um pagamento nunca é apagado, e por isso `REFUNDED` é um
 * estado e não a ausência do registro. */
export type PaymentStatus = "REPORTED" | "CONFIRMED" | "REFUSED" | "REFUNDED" | "CHARGED_BACK";

/** Um recebimento do estúdio.
 *
 * **Valor é texto**, como em todo o resto do projeto: a API devolve decimal
 * exato e converter para `number` reintroduziria o arredondamento binário que o
 * `Numeric(12, 2)` do banco existe para evitar.
 *
 * `retainedAt` não é o mesmo que devolvido. Um sinal retido continua
 * `CONFIRMED` — o estúdio ficou com ele para compensar o horário reservado
 * (RN-AGE-009) —, e só um valor devolvido saiu do caixa. Uma tela que mostrasse
 * apenas o estado contaria a metade errada da história. */
export interface Payment {
  id: string;
  bookingId: string | null;
  sessionId: string | null;
  clientId: string | null;
  amount: string;
  kind: PaymentKind;
  method: PaymentMethod;
  status: PaymentStatus;
  note: string | null;
  reportedAt: string;
  confirmedAt: string | null;
  refusedAt: string | null;
  refusalReason: string | null;
  retainedAt: string | null;
  retainedReason: string | null;
}
