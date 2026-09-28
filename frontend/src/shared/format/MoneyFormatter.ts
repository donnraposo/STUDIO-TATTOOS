/** Valores em euro, na forma que o estúdio lê.
 *
 * A API devolve dinheiro como **texto decimal** — `"1000.00"` —, e não como
 * número, de propósito: `Numeric(12, 2)` no banco existe justamente para que
 * nenhum arredondamento binário toque em repasse. Converter para `number` aqui
 * reintroduziria o problema que o backend evitou.
 *
 * Por isso a formatação recebe `string` e só converte no último instante, para
 * exibir. Nenhuma conta é feita nesta camada: soma e percentual são do backend,
 * que é quem responde pelo valor pago a alguém. */
export class MoneyFormatter {
  private static readonly LOCALE = "en-IE";
  private static readonly CURRENCY = "EUR";

  private readonly format: Intl.NumberFormat;

  constructor() {
    this.format = new Intl.NumberFormat(MoneyFormatter.LOCALE, {
      style: "currency",
      currency: MoneyFormatter.CURRENCY,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  /** `"1000.00"` vira `€1,000.00`. Texto inválido devolve traço em vez de
   * `NaN`: um campo vazio na tela é melhor do que uma palavra que parece um
   * defeito do sistema. */
  amount(value: string | null | undefined): string {
    if (value === null || value === undefined || value.trim() === "") {
      return "—";
    }

    const parsed = Number(value);
    return Number.isFinite(parsed) ? this.format.format(parsed) : "—";
  }

  /** `"70.00"` vira `70%`. O percentual do artista é inteiro na prática, e
   * mostrar `70.00%` só acrescentaria ruído. */
  percentage(value: string | null | undefined): string {
    if (value === null || value === undefined || value.trim() === "") {
      return "—";
    }

    const parsed = Number(value);
    return Number.isFinite(parsed) ? `${Number(parsed.toFixed(2))}%` : "—";
  }
}
