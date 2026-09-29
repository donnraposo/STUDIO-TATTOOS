/** O rascunho como o formulário o mantém: tudo texto, porque é o que um campo
 * devolve. A conversão para número só acontece na borda, ao enviar. */
export interface QuoteDraftInput {
  clientId: string;
  description: string;
  bodyRegion: string;
  sizeEstimate: string;
  totalValue: string;
  plannedSessions: string;
  plannedValuePerSession: string;
  estimatedDurationMinutes: string;
  notes: string;
}

export type QuoteDraftField = keyof QuoteDraftInput;

export interface QuoteDraftReport {
  errors: Partial<Record<QuoteDraftField, string>>;
  submittable: boolean;
  /** Sessões previstas × valor previsto por sessão, em texto decimal exato.
   * Nulo quando um dos dois ainda não é um valor utilizável. */
  plannedTotal: string | null;
  /** O planejado passa do valor total (RN-PAG-001). */
  exceedsTotal: boolean;
  /** O planejado não fecha com o valor total, para mais ou para menos. */
  differsFromTotal: boolean;
}

/** Conferência do rascunho de orçamento, antes de enviar.
 *
 * Repete os limites do `QuoteFieldsRequest` de propósito: o backend recusa por
 * último e continua sendo quem garante, mas quem está digitando merece saber
 * qual campo está errado antes de perder o formulário inteiro num 422.
 *
 * **A soma das sessões é conferida em centavos inteiros, não em ponto
 * flutuante.** Três sessões de €133,33 somam €399,99 — em `number`, somam
 * 399.99000000000007, e a tela acusaria diferença onde não há. É o mesmo
 * cuidado que levou o backend a usar decimal exato, aplicado aqui por coerência
 * e não por capricho.
 *
 * **A diferença entre o planejado e o total não impede o envio.** A RN-PAG-001
 * diz que a soma das sessões não pode passar do total aprovado, e o backend
 * hoje não recusa esse caso; bloquear aqui criaria uma trava que só existe no
 * navegador — e que passaria a impressão de uma garantia que o sistema não tem.
 * O aviso informa; o que impede é o que o servidor recusa. */
export class QuoteDraftCheck {
  private static readonly AMOUNT = /^\d+(\.\d{1,2})?$/;
  private static readonly COUNT = /^\d+$/;
  private static readonly SHORT_TEXT_LIMIT = 80;
  private static readonly NOTES_LIMIT = 2000;
  private static readonly CENTS_IN_UNIT = 100;

  /** `requiresClient` é falso na edição: reatribuir o orçamento a outro cliente
   * não é editar, e o campo nem aparece. */
  review(input: QuoteDraftInput, requiresClient: boolean): QuoteDraftReport {
    const errors: Partial<Record<QuoteDraftField, string>> = {};

    if (requiresClient && input.clientId === "") {
      errors.clientId = "Choose the client this quote is for.";
    }

    this.checkText(errors, "description", input.description, Number.POSITIVE_INFINITY);
    this.checkText(errors, "bodyRegion", input.bodyRegion, QuoteDraftCheck.SHORT_TEXT_LIMIT);
    this.checkText(errors, "sizeEstimate", input.sizeEstimate, QuoteDraftCheck.SHORT_TEXT_LIMIT);
    this.checkAmount(errors, "totalValue", input.totalValue);
    this.checkAmount(errors, "plannedValuePerSession", input.plannedValuePerSession);
    this.checkCount(errors, "plannedSessions", input.plannedSessions);
    this.checkCount(errors, "estimatedDurationMinutes", input.estimatedDurationMinutes);

    if (input.notes.trim().length > QuoteDraftCheck.NOTES_LIMIT) {
      errors.notes = `Keep the notes under ${QuoteDraftCheck.NOTES_LIMIT} characters.`;
    }

    const planned = this.plannedCents(input);
    const total = QuoteDraftCheck.toCents(input.totalValue);

    return {
      errors,
      submittable: Object.keys(errors).length === 0,
      plannedTotal: planned === null ? null : QuoteDraftCheck.fromCents(planned),
      exceedsTotal: planned !== null && total !== null && planned > total,
      differsFromTotal: planned !== null && total !== null && planned !== total,
    };
  }

  private checkText(
    errors: Partial<Record<QuoteDraftField, string>>,
    field: QuoteDraftField,
    value: string,
    limit: number,
  ): void {
    const trimmed = value.trim();
    if (trimmed === "") {
      errors[field] = "This field is required.";
    } else if (trimmed.length > limit) {
      errors[field] = `Keep it under ${limit} characters.`;
    }
  }

  private checkAmount(
    errors: Partial<Record<QuoteDraftField, string>>,
    field: QuoteDraftField,
    value: string,
  ): void {
    const cents = QuoteDraftCheck.toCents(value);
    if (cents === null) {
      errors[field] = "Use an amount in euro, with up to two decimals.";
    } else if (cents === 0) {
      errors[field] = "The amount must be greater than zero.";
    }
  }

  private checkCount(
    errors: Partial<Record<QuoteDraftField, string>>,
    field: QuoteDraftField,
    value: string,
  ): void {
    const trimmed = value.trim();
    if (!QuoteDraftCheck.COUNT.test(trimmed) || Number(trimmed) < 1) {
      errors[field] = "Use a whole number, at least one.";
    }
  }

  private plannedCents(input: QuoteDraftInput): number | null {
    const perSession = QuoteDraftCheck.toCents(input.plannedValuePerSession);
    const sessions = input.plannedSessions.trim();
    if (perSession === null || perSession === 0 || !QuoteDraftCheck.COUNT.test(sessions)) {
      return null;
    }
    const count = Number(sessions);
    return count < 1 ? null : perSession * count;
  }

  /** Texto decimal para centavos inteiros. Recusa sinal, expoente e mais de duas
   * casas — formas que um campo de dinheiro não deveria produzir e que, aceitas
   * em silêncio, virariam um valor diferente do que foi digitado. */
  private static toCents(value: string): number | null {
    const trimmed = value.trim();
    if (!QuoteDraftCheck.AMOUNT.test(trimmed)) {
      return null;
    }
    const [whole, fraction = ""] = trimmed.split(".");
    return Number(whole) * QuoteDraftCheck.CENTS_IN_UNIT + Number(fraction.padEnd(2, "0"));
  }

  private static fromCents(cents: number): string {
    const units = Math.trunc(cents / QuoteDraftCheck.CENTS_IN_UNIT);
    const remainder = cents % QuoteDraftCheck.CENTS_IN_UNIT;
    return `${units}.${String(remainder).padStart(2, "0")}`;
  }
}
