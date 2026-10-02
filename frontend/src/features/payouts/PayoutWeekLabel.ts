import { StudioClock } from "@/shared/format/StudioClock";

/** Como uma semana de repasse se escreve na tela (RN-REP-004).
 *
 * A semana vai de sexta 20h a sexta 20h, e mostrar os dois instantes crus —
 * "25 Sept 2026, 20:00 – 02 Oct 2026, 20:00" — faria o artista ler duas datas e
 * deduzir o período. O rótulo diz a semana de uma vez.
 *
 * **Formata no fuso do estúdio**, nunca no do navegador. A API devolve o
 * fechamento em UTC, e às 20h de Dublin no verão isso é 19h UTC: um artista
 * consultando de outro país veria a semana terminar numa hora que não existe no
 * estúdio — e, na virada do dia, num dia errado.
 *
 * Classe pura: não conhece Vue nem API. */
export class PayoutWeekLabel {
  private readonly clock: StudioClock;

  constructor(clock: StudioClock = new StudioClock()) {
    this.clock = clock;
  }

  /** `26 Sept – 2 Oct 2026`.
   *
   * O começo exclui o dia da sexta anterior porque a semana **abre** às 20h dela:
   * o primeiro dia inteiro de trabalho é o sábado. Mostrar a sexta anterior faria
   * o artista procurar nela um atendimento que pertence ao repasse passado. */
  of(periodStart: string, periodEnd: string): string {
    const firstDay = new Date(new Date(periodStart).getTime() + PayoutWeekLabel.ONE_DAY_MS);
    return `${this.clock.date(firstDay.toISOString())} – ${this.clock.date(periodEnd)}`;
  }

  /** O instante exato do fechamento, para quem precisa conferir a borda. */
  closing(periodEnd: string): string {
    return this.clock.dateTime(periodEnd);
  }

  private static readonly ONE_DAY_MS = 24 * 60 * 60 * 1000;
}
