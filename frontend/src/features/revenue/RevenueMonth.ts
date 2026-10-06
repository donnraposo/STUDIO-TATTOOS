/** O mês que a tela está mostrando, e como andar entre eles (RN 10.4).
 *
 * Ano e mês viajam como dois números, e não como `Date`: um `Date` carrega dia,
 * hora e fuso, e "outubro de 2026" não tem nenhuma das três coisas. Montá-lo
 * para depois ignorar dois terços dele é o caminho curto para somar um mês e
 * cair em 1º de março porque fevereiro tem 28 dias.
 *
 * **O mês corrente vem do fuso do estúdio, não do navegador.** Um gestor
 * abrindo a tela à meia-noite e meia de 1º de novembro em Dublin, com o
 * navegador em Lisboa, veria outubro — e concluiria que o mês não virou.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class RevenueMonth {
  private static readonly TIME_ZONE = "Europe/Dublin";
  private static readonly LOCALE = "en-IE";

  /** O mês corrente no fuso do estúdio. */
  current(now: Date = new Date()): { year: number; month: number } {
    const parts = new Intl.DateTimeFormat(RevenueMonth.LOCALE, {
      timeZone: RevenueMonth.TIME_ZONE,
      year: "numeric",
      month: "numeric",
    }).formatToParts(now);

    return {
      year: Number(parts.find((part) => part.type === "year")?.value),
      month: Number(parts.find((part) => part.type === "month")?.value),
    };
  }

  previous(year: number, month: number): { year: number; month: number } {
    return month === 1 ? { year: year - 1, month: 12 } : { year, month: month - 1 };
  }

  next(year: number, month: number): { year: number; month: number } {
    return month === 12 ? { year: year + 1, month: 1 } : { year, month: month + 1 };
  }

  /** `2026, 10` vira `October 2026`. */
  label(year: number, month: number): string {
    return new Intl.DateTimeFormat(RevenueMonth.LOCALE, {
      month: "long",
      year: "numeric",
      timeZone: "UTC",
    }).format(new Date(Date.UTC(year, month - 1, 1)));
  }

  /** `2026, 10` vira `Oct`, para a comparação entre meses caber na tela. */
  shortLabel(year: number, month: number): string {
    return new Intl.DateTimeFormat(RevenueMonth.LOCALE, {
      month: "short",
      timeZone: "UTC",
    }).format(new Date(Date.UTC(year, month - 1, 1)));
  }

  /** Não há faturamento no futuro, e oferecer o mês seguinte levaria o gestor a
   * uma tela vazia que ele leria como defeito. */
  isAfter(year: number, month: number, limit: { year: number; month: number }): boolean {
    return year > limit.year || (year === limit.year && month > limit.month);
  }
}
