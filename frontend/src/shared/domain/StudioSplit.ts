import type { QuoteOrigin } from "@/shared/domain/Quote";

/** A divisão entre artista e estúdio, dita pelos dois lados (RN-REP-001,
 * RN-REP-002 e ADR-030).
 *
 * **Existe porque a mesma divisão era escrita em três lugares.** O
 * `QuoteDisplay` guardava 70 e 50, o `AccountDisplay` calculava o complemento,
 * e o formulário de agendamento trazia a terceira cópia — com os números do
 * lado do estúdio, 30 e 50. Três versões da mesma regra divergem na primeira
 * renegociação, e a que fica para trás é a que alguém vai ler.
 *
 * **Dois lados porque o estúdio fala por um e o sistema grava o outro.** Os
 * acordos são enunciados como "30% se o cliente foi trazido pelo tatuador, 50%
 * se foi indicação, 15% em condições especiais" — percentuais da casa. O que
 * fica gravado é o do artista: 70, 50 e 85. Mostrar os dois ao mesmo tempo é o
 * que impede digitar 30 querendo dizer "a casa fica com 30".
 *
 * **É informação, não decisão.** Quem congela o percentual é o backend, na
 * aprovação (RN-REP-006), e o que vale depois é o que vem na resposta — nunca
 * este cálculo. Divergindo, a tela é que está errada.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class StudioSplit {
  private static readonly ARTIST_BY_ORIGIN: Record<QuoteOrigin, string> = {
    ARTIST_OWN: "70",
    STUDIO_REFERRAL: "50",
  };

  /** O que o artista fica, quando não há acordo próprio. */
  artistShareFor(origin: QuoteOrigin): string {
    return StudioSplit.ARTIST_BY_ORIGIN[origin];
  }

  /** O que a casa fica, dado o percentual do artista. `"70"` vira `"30%"`.
   *
   * Texto vazio ou ilegível devolve traço: um `NaN%` ao lado do campo enquanto
   * alguém digita parece defeito do sistema. */
  studioShareOf(artistPercentage: string): string {
    const parsed = Number(artistPercentage);
    if (artistPercentage.trim() === "" || !Number.isFinite(parsed)) {
      return "—";
    }
    return `${Number((100 - parsed).toFixed(2))}%`;
  }

  /** O que a casa fica nesta origem, sem acordo próprio. `ARTIST_OWN` vira
   * `"30%"` — que é como o estúdio enuncia o acordo. */
  studioShareForOrigin(origin: QuoteOrigin): string {
    return this.studioShareOf(this.artistShareFor(origin));
  }
}
