import { describe, expect, it } from "vitest";

import { BookingDeposit } from "@/features/payments/BookingDeposit";
import type { Payment } from "@/shared/domain/Payment";

/** RN-PAG-001, RN-AGE-005 e RN-AGE-008. O que mais importa aqui é a diferença
 * entre informado e confirmado: é ela que decide se o botão de aprovar o
 * horário vai funcionar ou devolver 403, e até esta etapa o gestor só descobria
 * pelo erro.
 */

function payment(fields: Partial<Payment> = {}): Payment {
  return {
    id: "p1",
    bookingId: "b1",
    sessionId: null,
    clientId: "c1",
    amount: "50.00",
    kind: "DEPOSIT",
    method: "BANK_TRANSFER",
    status: "CONFIRMED",
    note: null,
    reportedAt: "2026-10-01T10:00:00Z",
    confirmedAt: "2026-10-01T11:00:00Z",
    refusedAt: null,
    refusalReason: null,
    retainedAt: null,
    retainedReason: null,
    ...fields,
  };
}

describe("BookingDeposit", () => {
  const deposit = new BookingDeposit();

  it("keeps the amount the rule fixed", () => {
    expect(BookingDeposit.AMOUNT).toBe("50.00");
  });

  it("finds the deposit that is still standing", () => {
    expect(deposit.live([payment({ status: "REPORTED" })])?.status).toBe("REPORTED");
    expect(deposit.live([payment({ status: "CONFIRMED" })])?.status).toBe("CONFIRMED");
  });

  /** Depois de uma recusa o cliente paga outro, e depois de remarcar fora do
   * prazo ele precisa pagar um novo (RN-AGE-008). Contá-los como vivos
   * esconderia o botão que lança o substituto. */
  it("does not count a refused or refunded deposit as standing", () => {
    expect(deposit.live([payment({ status: "REFUSED" })])).toBeNull();
    expect(deposit.live([payment({ status: "REFUNDED" })])).toBeNull();
  });

  it("offers a new deposit only when none is standing", () => {
    expect(deposit.canRegisterDeposit([])).toBe(true);
    expect(deposit.canRegisterDeposit([payment({ status: "REFUSED" })])).toBe(true);
    expect(deposit.canRegisterDeposit([payment({ status: "REPORTED" })])).toBe(false);
    expect(deposit.canRegisterDeposit([payment({ status: "CONFIRMED" })])).toBe(false);
  });

  /** O teste que mais importa deste arquivo. A RN-AGE-005 pede recebimento
   * **confirmado**; informado não basta, e é essa diferença que o 403 do botão
   * de aprovar estava comunicando sozinho. */
  it("does not treat a reported deposit as enough to approve the booking", () => {
    expect(deposit.isSatisfied([payment({ status: "REPORTED" })])).toBe(false);
    expect(deposit.isSatisfied([payment({ status: "CONFIRMED" })])).toBe(true);
  });

  it("has nothing to satisfy a booking with no payment at all", () => {
    expect(deposit.isSatisfied([])).toBe(false);
  });

  /** RN-PAG-004: quem pagou a tatuagem inteira antecipadamente não deve um
   * sinal. Ignorar o pagamento integral mostraria "nothing received" num
   * agendamento cujo valor todo já entrou. */
  it("accepts a confirmed full prepayment in place of the deposit", () => {
    const prepaid = [payment({ kind: "FULL_PREPAY", amount: "1000.00" })];

    expect(deposit.prepayment(prepaid)?.amount).toBe("1000.00");
    expect(deposit.isSatisfied(prepaid)).toBe(true);
  });

  it("ignores a payment that belongs to a session, not to the booking", () => {
    expect(deposit.live([payment({ kind: "BALANCE" })])).toBeNull();
    expect(deposit.isSatisfied([payment({ kind: "BALANCE" })])).toBe(false);
  });
});
