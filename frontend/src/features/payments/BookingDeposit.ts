import type { Payment } from "@/shared/domain/Payment";

/** O sinal de um agendamento, lido a partir dos pagamentos dele (RN-PAG-001 e
 * RN-AGE-005).
 *
 * **Um sinal vivo por agendamento.** Vivo é informado ou confirmado; recusado e
 * devolvido não contam, porque depois de uma recusa o cliente paga outro, e
 * depois de remarcar fora do prazo ele precisa pagar um novo (RN-AGE-008). É a
 * mesma leitura que o backend faz para recusar um segundo lançamento, e por
 * isso a tela não oferece o botão onde o servidor diria não.
 *
 * **Confirmado é o que libera a aprovação do horário.** Informado não basta: a
 * RN-AGE-005 pede confirmação, e é justamente a diferença entre as duas coisas
 * que faz o botão de aprovar devolver 403 para quem não sabe disso.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class BookingDeposit {
  /** O valor da RN-PAG-001. Texto, como todo dinheiro no projeto. */
  static readonly AMOUNT = "50.00";

  private static readonly LIVE = ["REPORTED", "CONFIRMED"];

  /** O sinal que ainda está de pé, se houver. */
  live(payments: Payment[]): Payment | null {
    return (
      payments.find(
        (payment) =>
          payment.kind === "DEPOSIT" && BookingDeposit.LIVE.includes(payment.status),
      ) ?? null
    );
  }

  /** O pagamento integral antecipado (RN-PAG-004), quando o cliente o fez.
   *
   * Conta como recebimento do horário tanto quanto o sinal, e por isso a tela
   * precisa mostrá-lo — sem isso o gestor veria "no deposit" num agendamento
   * cujo valor inteiro já entrou. */
  prepayment(payments: Payment[]): Payment | null {
    return (
      payments.find(
        (payment) =>
          payment.kind === "FULL_PREPAY" && BookingDeposit.LIVE.includes(payment.status),
      ) ?? null
    );
  }

  /** Verdadeiro quando há recebimento **confirmado** para este horário. */
  isSatisfied(payments: Payment[]): boolean {
    return [this.live(payments), this.prepayment(payments)].some(
      (payment) => payment?.status === "CONFIRMED",
    );
  }

  /** Lançar um sinal novo só faz sentido se não houver um de pé. O servidor
   * recusa o segundo, e oferecer o botão ensinaria a equipe a desconfiar dos
   * próprios botões. */
  canRegisterDeposit(payments: Payment[]): boolean {
    return this.live(payments) === null;
  }
}
