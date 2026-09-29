/** Estados do orçamento (RN-ORC-002 e RN-ORC-003).
 *
 * Não há vencimento automático: o orçamento fica em `PENDING` até uma decisão
 * manual, pelo tempo que for. E o ciclo não é de mão única — alterar um
 * aprovado o devolve a `PENDING` e exige nova aprovação. */
export type QuoteStatus = "PENDING" | "APPROVED" | "REJECTED";

/** Origem do atendimento (RN-CLI-002, RN-REP-001 e RN-REP-002).
 *
 * É o campo que decide o dinheiro: cliente do próprio artista divide 70/30,
 * indicação do estúdio divide 50/50. */
export type QuoteOrigin = "ARTIST_OWN" | "STUDIO_REFERRAL";

/** Os campos editáveis de um orçamento (RN-ORC-004).
 *
 * Valores monetários são **texto**, não número: a API os devolve assim porque o
 * banco usa decimal exato, e converter para `number` reintroduziria o
 * arredondamento binário que o backend evitou. A interface só formata. */
export interface QuoteFields {
  origin: QuoteOrigin;
  description: string;
  bodyRegion: string;
  sizeEstimate: string;
  totalValue: string;
  plannedSessions: number;
  plannedValuePerSession: string;
  estimatedDurationMinutes: number;
  notes: string | null;
}

export interface Quote extends QuoteFields {
  id: string;
  clientId: string;
  artistId: string;
  status: QuoteStatus;
  /** Congelado na aprovação (RN-REP-006). Nulo enquanto pendente — e é isso que
   * permite à tela mostrar o percentual acordado sem recalcular nada, portanto
   * sem risco de exibir número diferente do que será pago. */
  artistPercentage: string | null;
  approvedAt: string | null;
  rejectionReason: string | null;
  rejectionNote: string | null;
  createdAt: string;
}

/** Imagem de referência (RN-ORC-004).
 *
 * `contentPath` é o caminho autenticado que devolve a imagem. Não é endereço
 * assinado nem temporário: ele só responde com o cookie de sessão. */
export interface ReferenceImage {
  id: string;
  contentType: string;
  byteSize: number;
  uploadedAt: string;
  contentPath: string;
}
