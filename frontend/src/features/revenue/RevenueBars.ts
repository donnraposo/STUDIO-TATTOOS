import type { MonthlyRevenue } from "@/shared/domain/Revenue";

/** A altura de cada barra na comparação entre meses.
 *
 * **Geometria em classe pura**, como o `BookingPlacement` da agenda: é conta, é
 * testável sem montar tela, e é onde um erro passa despercebido — uma barra com
 * a proporção errada não quebra nada, só mente.
 *
 * A escala é relativa ao maior mês do período, e não a um teto fixo: o estúdio
 * compara meses entre si, e um eixo absoluto faria todos os meses parecerem
 * iguais num ano fraco e todos rasteiros num mês excepcional.
 *
 * **Mês zerado recebe altura zero, e continua desenhado.** Sumir com ele faria
 * o gráfico mentir sobre o tempo.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class RevenueBars {
  /** Percentual da altura disponível, de 0 a 100. */
  heights(months: MonthlyRevenue[]): number[] {
    const values = months.map((each) => Number(each.totals.value));
    const tallest = Math.max(...values, 0);

    if (tallest <= 0) {
      return values.map(() => 0);
    }

    return values.map((value) => (Number.isFinite(value) ? (value / tallest) * 100 : 0));
  }

  /** O mês de maior faturamento, para a tela poder destacá-lo. Nulo quando não
   * houve faturamento nenhum: destacar um zero entre zeros não diz nada. */
  best(months: MonthlyRevenue[]): MonthlyRevenue | null {
    const earning = months.filter((each) => Number(each.totals.value) > 0);
    if (earning.length === 0) {
      return null;
    }

    return earning.reduce((best, each) =>
      Number(each.totals.value) > Number(best.totals.value) ? each : best,
    );
  }
}
