/** Datas e horas no fuso do estúdio, `Europe/Dublin`.
 *
 * **O fuso é fixo e não é o do navegador.** A agenda pertence a um estúdio em
 * Cork; um artista consultando o celular de outro país precisa ver o horário do
 * estúdio, não o dele. Formatar com o fuso local do navegador produziria uma
 * agenda deslocada que parece certa — a pior espécie de erro, porque ninguém
 * desconfia dela.
 *
 * Usa `Intl` em vez de biblioteca de data: a plataforma já conhece a regra do
 * horário de verão irlandês e a mantém atualizada. Uma dependência aqui
 * carregaria a mesma informação, com risco de ficar velha.
 *
 * Toda entrada é o texto ISO que a API devolve, com deslocamento. */
export class StudioClock {
  static readonly TIME_ZONE = "Europe/Dublin";
  private static readonly LOCALE = "en-IE";

  private readonly timeFormat: Intl.DateTimeFormat;
  private readonly dateFormat: Intl.DateTimeFormat;
  private readonly dateTimeFormat: Intl.DateTimeFormat;
  private readonly partsFormat: Intl.DateTimeFormat;
  private readonly dayFormat: Intl.DateTimeFormat;

  constructor(timeZone: string = StudioClock.TIME_ZONE) {
    const locale = StudioClock.LOCALE;
    this.timeFormat = new Intl.DateTimeFormat(locale, {
      timeZone,
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    this.dateFormat = new Intl.DateTimeFormat(locale, {
      timeZone,
      weekday: "short",
      day: "numeric",
      month: "short",
    });
    this.dateTimeFormat = new Intl.DateTimeFormat(locale, {
      timeZone,
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    this.partsFormat = new Intl.DateTimeFormat(locale, {
      timeZone,
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    /** `en-CA` porque é o único locale corrente que formata data como
     * `YYYY-MM-DD` nativamente. Montar a partir das partes daria o mesmo
     * resultado com três linhas a mais e um `padStart` a esquecer. */
    this.dayFormat = new Intl.DateTimeFormat("en-CA", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  }

  /** `14:30` */
  time(iso: string): string {
    return this.timeFormat.format(new Date(iso));
  }

  /** `Tue, 6 Oct` */
  date(iso: string): string {
    return this.dateFormat.format(new Date(iso));
  }

  /** `06 Oct 2026, 14:30` */
  dateTime(iso: string): string {
    return this.dateTimeFormat.format(new Date(iso));
  }

  /** `2026-10-06` — o dia **no estúdio**, na forma que um campo de data usa.
   *
   * É o que liga um instante a uma agenda: a reserva das 00h30 de terça em
   * Dublin pertence a terça, e `toISOString().slice(0, 10)` a colocaria na
   * segunda, porque aquele instante ainda é segunda em UTC. O erro tem uma hora
   * de largura e aparece só de madrugada e só em parte do ano — o tipo de
   * defeito que ninguém reproduz quando é relatado. */
  dayKey(iso: string): string {
    return this.dayFormat.format(new Date(iso));
  }

  /** O dia de hoje no estúdio, pela mesma régua. */
  today(now: Date = new Date()): string {
    return this.dayFormat.format(now);
  }

  /** Minutos desde a meia-noite **no estúdio**.
   *
   * É a medida de que a timeline precisa para posicionar um bloco, e é onde o
   * horário de verão morde: o mesmo instante cai em minutos diferentes conforme
   * a data do ano. Calcular a partir do relógio do navegador daria a resposta
   * certa só para quem estivesse na Irlanda. */
  minutesSinceMidnight(iso: string): number {
    const parts = this.partsFormat.formatToParts(new Date(iso));
    const hour = Number(parts.find((part) => part.type === "hour")?.value ?? "0");
    const minute = Number(parts.find((part) => part.type === "minute")?.value ?? "0");
    return hour * 60 + minute;
  }
}
