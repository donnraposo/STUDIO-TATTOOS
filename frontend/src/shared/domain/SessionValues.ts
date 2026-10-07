/** O valor total e o valor por sessão, que são o mesmo fato dito de duas
 * formas (RN-ORC-004 e RN-PAG-001).
 *
 * **Quem preenche um não precisa preencher o outro.** Pedir os dois é pedir ao
 * tatuador que faça uma conta que o sistema faz — e abrir a chance de os dois
 * números discordarem, que é pior do que não ter um deles: o repasse sai de um
 * e o orçamento aprovado do outro.
 *
 * **Em centavos inteiros, nunca em ponto flutuante.** `0.1 + 0.2` não dá `0.3`
 * em binário, e aqui o resultado vira o que alguém recebe. É a mesma razão pela
 * qual a API devolve dinheiro como texto.
 *
 * **A divisão arredonda para baixo.** A RN-PAG-001 diz que a soma dos sinais e
 * saldos das sessões não pode ultrapassar o valor total aprovado; dividindo
 * €1.000 em três, €333,34 por sessão somaria €1.000,02 e estouraria o teto.
 * €333,33 soma €999,99 e fica dentro — a diferença de centavos é o estúdio
 * cobrando a menos, não a mais.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class SessionValues {
  /** O valor de cada sessão, a partir do total. Texto vazio ou inválido
   * devolve vazio: um campo que se preenche sozinho com `NaN` enquanto alguém
   * digita parece defeito do sistema. */
  perSessionFrom(total: string, sessions: number): string {
    const cents = SessionValues.toCents(total);
    if (cents === null || sessions < 1) {
      return "";
    }
    return SessionValues.toText(Math.floor(cents / sessions));
  }

  /** O total, a partir do valor de cada sessão. Multiplicação é exata em
   * centavos, e por isso este caminho não perde nada. */
  totalFrom(perSession: string, sessions: number): string {
    const cents = SessionValues.toCents(perSession);
    if (cents === null || sessions < 1) {
      return "";
    }
    return SessionValues.toText(cents * sessions);
  }

  /** Há valor suficiente para orçar: basta um dos dois preenchido. */
  isComplete(total: string, perSession: string): boolean {
    return (SessionValues.toCents(total) ?? 0) > 0 || (SessionValues.toCents(perSession) ?? 0) > 0;
  }

  private static toCents(value: string): number | null {
    if (value.trim() === "") {
      return null;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.round(parsed * 100) : null;
  }

  private static toText(cents: number): string {
    return (cents / 100).toFixed(2);
  }
}
