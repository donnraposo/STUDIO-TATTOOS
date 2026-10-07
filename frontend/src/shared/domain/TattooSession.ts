/** Estados da sessão (RN-ORC-005 e RN-ORC-006).
 *
 * **`DONE` e `PAID_OFF` são separados de propósito.** O artista marca que a
 * sessão aconteceu; o gestor confirma quanto entrou. Só depois das duas ela
 * entra em repasse — um estado único colocaria trabalho ainda não pago no
 * fechamento de sexta.
 *
 * `PARTIALLY_DONE` existe porque sessão interrompida gera repasse apenas sobre
 * o valor efetivamente recebido, não sobre o previsto. */
export type SessionStatus =
  | "SCHEDULED"
  | "DONE"
  | "PARTIALLY_DONE"
  | "PAID_OFF"
  | "CANCELLED"
  | "NO_SHOW";

/** Uma sessão prevista pelo orçamento, e a unidade de cálculo do repasse.
 *
 * **Valores são texto**, como em todo o resto do projeto: a API devolve decimal
 * exato e converter para `number` reintroduziria o arredondamento binário que o
 * `Numeric(12, 2)` do banco existe para evitar.
 *
 * `origin` e `artistPercentage` são **cópias congeladas** do orçamento no
 * momento da aprovação (RN-REP-006). O orçamento pode ter voltado a pendente e
 * sido reaprovado com outro percentual desde então; o que vale para esta sessão
 * é o que está aqui.
 *
 * `chargedValue` vem nulo enquanto a sessão está agendada. Preenchido, é o que
 * realmente entrou — a base do repasse numa sessão parcial (RN-ORC-006). */
export interface TattooSession {
  id: string;
  quoteId: string;
  sequenceNumber: number;
  status: SessionStatus;
  origin: string;
  plannedValue: string;
  chargedValue: string | null;
  artistPercentage: string;
  performedAt: string | null;
  markedDoneBy: string | null;
  confirmedAt: string | null;
  confirmedBy: string | null;
  createdAt: string;
}
