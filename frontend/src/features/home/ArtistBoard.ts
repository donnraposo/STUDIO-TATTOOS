import type { Booking } from "@/shared/domain/Booking";
import type { Payout } from "@/shared/domain/Payout";
import type { Quote } from "@/shared/domain/Quote";

/** O dia do artista, montado a partir do que ele já pode ver (seção 10.2 e
 * 10.3).
 *
 * **Nada é filtrado por artista aqui.** O backend devolve o recorte certo —
 * `ListBookings` diz que o artista vê apenas a própria agenda, a RN-REP-004 diz
 * o mesmo do repasse, e a RN-CLI-004 do cliente. Refiltrar no navegador daria
 * duas versões da mesma regra, e a do navegador seria a que ficaria para trás.
 *
 * O que esta classe faz é **ordenar e contar**: o que vem agora, o que está
 * parado esperando o estúdio, e quanto entrou no último fechamento.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class ArtistBoard {
  /** Os compromissos de hoje, do mais cedo para o mais tarde.
   *
   * Cancelado e recusado ficam de fora: o artista quer saber o que vai
   * acontecer, e um horário recusado na lista do dia o faria procurar um
   * cliente que não vem. */
  today(bookings: Booking[]): Booking[] {
    return bookings
      .filter((booking) => ["REQUESTED", "APPROVED"].includes(booking.status))
      .slice()
      .sort((first, second) => first.startsAt.localeCompare(second.startsAt));
  }

  /** O próximo compromisso ainda por vir, ou nulo quando o dia acabou.
   *
   * Compara instantes em ISO, que o backend devolve em UTC — comparar texto de
   * hora local daria resultados diferentes conforme o fuso de quem olha. */
  next(bookings: Booking[], now: string): Booking | null {
    return this.today(bookings).find((booking) => booking.endsAt > now) ?? null;
  }

  /** O que o artista pediu e o estúdio ainda não decidiu.
   *
   * É a contraparte da fila do gestor: do lado dele é trabalho a fazer, do lado
   * do artista é espera — e é a pergunta que ele faria ao gerente no corredor. */
  awaitingDecision(bookings: Booking[]): number {
    return bookings.filter((booking) => booking.status === "REQUESTED").length;
  }

  /** Orçamentos próprios ainda por aprovar (RN-ORC-002). O guest não tem
   * nenhum, porque não acessa o módulo (RN-ORC-001). */
  quotesPending(quotes: Quote[]): number {
    return quotes.filter((quote) => quote.status === "PENDING").length;
  }

  /** O último fechamento, que é o mais recente por data de término.
   *
   * **Não é previsão da semana corrente.** O repasse só existe depois do
   * fechamento de sexta às 20h (RN-REP-004), e um número calculado no navegador
   * para a semana em curso seria o sistema dizendo ao artista quanto ele vai
   * receber sem que ninguém tenha fechado nada. */
  lastPayout(payouts: Payout[]): Payout | null {
    return (
      payouts
        .slice()
        .sort((first, second) => second.periodEnd.localeCompare(first.periodEnd))[0] ?? null
    );
  }
}
