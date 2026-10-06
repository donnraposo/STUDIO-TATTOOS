/** Um atendimento no detalhamento do mês (RN 10.4).
 *
 * É a linha do controle que o estúdio mantinha em planilha: quando o dinheiro
 * entrou, de quem foi o trabalho, quanto o cliente pagou, quanto ficou com o
 * tatuador e quanto ficou com a casa.
 *
 * **Todo valor é texto**, como em todo o resto do projeto: a API devolve
 * decimal exato, e converter para `number` reintroduziria o arredondamento
 * binário que o `Numeric(12, 2)` existe para evitar. A tela não faz conta
 * nenhuma com eles — soma e divisão são do backend, que é quem responde pelo
 * valor pago a alguém.
 *
 * `percentage` é o **congelado** daquele atendimento (RN-REP-006), e não o
 * acordo vigente: é o que explica o mesmo artista aparecer em divisões
 * diferentes no mesmo mês. */
export interface RevenueLine {
  sessionId: string;
  artistId: string;
  settledAt: string;
  value: string;
  percentage: string;
  artistAmount: string;
  studioAmount: string;
  /** O repasse deste atendimento já foi transferido ao artista. É a coluna
   * "Status" da planilha — e não é o mesmo que ter entrado num fechamento. */
  transferred: boolean;
}

/** Os três números do rodapé. `artists` e `studio` somam `value`, e é assim que
 * o estúdio confere o mês. */
export interface RevenueTotals {
  sessions: number;
  value: string;
  artists: string;
  studio: string;
}

export interface RevenueReport {
  year: number;
  month: number;
  lines: RevenueLine[];
  totals: RevenueTotals;
}

/** Um mês na comparação. Só os totais: quem quer o detalhe abre o mês. */
export interface MonthlyRevenue {
  year: number;
  month: number;
  totals: RevenueTotals;
}
