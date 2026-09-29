/** Tamanho de arquivo na forma que uma pessoa lê.
 *
 * A API devolve bytes, e `1048576` não diz a ninguém se a imagem é grande. O
 * estúdio anexa fotos de referência tiradas no celular, então a escala que
 * importa vai de alguns quilobytes a poucos megabytes.
 *
 * Usa múltiplos de 1024 e não de 1000: é o que o sistema operacional mostra a
 * quem escolheu o arquivo, e divergir disso faria o mesmo arquivo aparecer com
 * dois tamanhos diferentes na mesma tela do usuário. */
export class ByteSize {
  private static readonly STEP = 1024;
  private static readonly UNITS = ["B", "KB", "MB", "GB"];

  /** `1536` vira `1.5 KB`. Bytes inteiros não ganham casa decimal: `900 B` é
   * mais claro que `900.0 B`. Valor inválido devolve traço, pela mesma razão do
   * `MoneyFormatter` — um campo vazio é melhor que `NaN` na tela. */
  human(bytes: number): string {
    if (!Number.isFinite(bytes) || bytes < 0) {
      return "—";
    }

    let value = bytes;
    let unit = 0;
    while (value >= ByteSize.STEP && unit < ByteSize.UNITS.length - 1) {
      value /= ByteSize.STEP;
      unit += 1;
    }

    const rounded = unit === 0 ? String(Math.round(value)) : value.toFixed(1).replace(/\.0$/, "");
    return `${rounded} ${ByteSize.UNITS[unit]}`;
  }
}
