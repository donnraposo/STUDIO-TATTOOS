import type { Booking } from "@/shared/domain/Booking";
import type { Payment } from "@/shared/domain/Payment";
import type { PendingWorkItem } from "@/shared/domain/PendingWork";
import type { Quote } from "@/shared/domain/Quote";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";
import { StudioClock } from "@/shared/format/StudioClock";

/** Monta a fila única do painel a partir das três origens (seção 10.1).
 *
 * Classe pura: não conhece a API, o Vue nem a sessão. Recebe as listas já
 * buscadas e devolve os itens prontos para desenhar, ordenados por quem espera
 * há mais tempo.
 *
 * **A ordem é do mais antigo para o mais recente**, e é o ponto inteiro da
 * área. Ordenar pelo mais recente mostraria primeiro o que acabou de chegar e
 * empurraria para o fim justamente o que está parado — que é o que o gestor
 * precisa ver antes de tudo.
 *
 * **O nome do cliente é cruzado aqui, no navegador.** A API devolve
 * identificadores, e a junção é sobre conjunto pequeno, como já se faz na
 * agenda. O gatilho para levá-la ao servidor é volume — quando a lista de
 * clientes deixar de caber numa requisição —, não estética. Sem nome, o item
 * ainda aparece: uma pendência sem rótulo é melhor do que uma pendência
 * escondida. */
export class PendingWorkAssembler {
  private readonly clock: StudioClock;
  private readonly money: MoneyFormatter;

  constructor(clock: StudioClock = new StudioClock(), money: MoneyFormatter = new MoneyFormatter()) {
    this.clock = clock;
    this.money = money;
  }

  assemble(sources: {
    bookings: Booking[];
    payments: Payment[];
    quotes: Quote[];
    clientNames: Record<string, string>;
  }): PendingWorkItem[] {
    return [
      ...sources.bookings.map((booking) => this.fromBooking(booking, sources.clientNames)),
      ...sources.payments.map((payment) => this.fromPayment(payment, sources.clientNames)),
      ...sources.quotes.map((quote) => this.fromQuote(quote, sources.clientNames)),
    ].sort((first, second) => first.since.localeCompare(second.since));
  }

  private fromBooking(booking: Booking, names: Record<string, string>): PendingWorkItem {
    return {
      id: booking.id,
      kind: "BOOKING",
      title: names[booking.clientId] ?? "Client",
      detail: `${this.clock.date(booking.startsAt)} · ${this.clock.time(
        booking.startsAt,
      )}–${this.clock.time(booking.endsAt)}`,
      since: booking.requestedAt,
      route: "schedule",
    };
  }

  /** O sinal aparece com o valor porque é ele que o gestor confere contra o
   * comprovante. Sem o valor, confirmar exigiria abrir o item para saber o quê. */
  private fromPayment(payment: Payment, names: Record<string, string>): PendingWorkItem {
    const who = payment.clientId ? (names[payment.clientId] ?? "Client") : "Studio";
    return {
      id: payment.id,
      kind: "PAYMENT",
      title: who,
      detail: `${this.money.amount(payment.amount)} · ${PendingWorkAssembler.KIND_LABEL[payment.kind]}`,
      since: payment.reportedAt,
      route: "schedule",
    };
  }

  private fromQuote(quote: Quote, names: Record<string, string>): PendingWorkItem {
    return {
      id: quote.id,
      kind: "QUOTE",
      title: names[quote.clientId] ?? "Client",
      detail: `${this.money.amount(quote.totalValue)} · ${quote.plannedSessions} session${
        quote.plannedSessions === 1 ? "" : "s"
      }`,
      since: quote.createdAt,
      route: "quotes",
    };
  }

  private static readonly KIND_LABEL: Record<Payment["kind"], string> = {
    DEPOSIT: "Deposit",
    BALANCE: "Balance",
    FULL_PREPAY: "Full prepayment",
    GUEST_WEEK: "Guest week",
  };
}
