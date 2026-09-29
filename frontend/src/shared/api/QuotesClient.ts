import { HttpClient } from "@/shared/api/HttpClient";
import type {
  Quote,
  QuoteFields,
  QuoteOrigin,
  QuoteStatus,
  ReferenceImage,
} from "@/shared/domain/Quote";

interface QuotePayload {
  id: string;
  client_id: string;
  artist_id: string;
  origin: string;
  description: string;
  body_region: string;
  size_estimate: string;
  total_value: string;
  planned_sessions: number;
  planned_value_per_session: string;
  estimated_duration_minutes: number;
  notes: string | null;
  status: string;
  artist_percentage: string | null;
  approved_at: string | null;
  rejection_reason: string | null;
  rejection_note: string | null;
  created_at: string;
}

interface ReferenceImagePayload {
  id: string;
  content_type: string;
  byte_size: number;
  uploaded_at: string;
  content_path: string;
}

/** Orçamentos e imagens de referência (`/quotes`).
 *
 * O guest não tem acesso a este módulo (RN-ORC-001) e recebe 403; a tela nem
 * oferece a rota, mas quem chegar por URL é recusado pelo backend. */
export class QuotesClient {
  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  async list(): Promise<Quote[]> {
    const payload = await this.http.get<QuotePayload[]>("/quotes");
    return payload.map(QuotesClient.toQuote);
  }

  async create(clientId: string, fields: QuoteFields, artistId: string | null): Promise<Quote> {
    return QuotesClient.toQuote(
      await this.http.post<QuotePayload>("/quotes", {
        client_id: clientId,
        artist_id: artistId,
        ...QuotesClient.toPayload(fields),
      }),
    );
  }

  /** Editar devolve o orçamento a pendente e descarta o percentual congelado
   * (RN-ORC-003 e RN-REP-006). Quem chama precisa avisar antes de salvar: quem
   * edita um valor não espera perder a aprovação junto. */
  async update(quoteId: string, fields: QuoteFields): Promise<Quote> {
    return QuotesClient.toQuote(
      await this.http.put<QuotePayload>(`/quotes/${quoteId}`, QuotesClient.toPayload(fields)),
    );
  }

  /** `artistPercentage` nulo usa o padrão da origem: 70% para cliente próprio,
   * 50% para indicação do estúdio. Informado, corrige o percentual **deste**
   * atendimento (RN-CLI-003). */
  async approve(quoteId: string, artistPercentage: string | null): Promise<Quote> {
    return QuotesClient.toQuote(
      await this.http.post<QuotePayload>(`/quotes/${quoteId}/approve`, {
        artist_percentage: artistPercentage,
      }),
    );
  }

  async reject(quoteId: string, reason: string, note: string | null): Promise<Quote> {
    return QuotesClient.toQuote(
      await this.http.post<QuotePayload>(`/quotes/${quoteId}/reject`, { reason, note }),
    );
  }

  async listImages(quoteId: string): Promise<ReferenceImage[]> {
    const payload = await this.http.get<ReferenceImagePayload[]>(
      `/quotes/${quoteId}/reference-images`,
    );
    return payload.map(QuotesClient.toImage);
  }

  async attachImage(quoteId: string, file: File): Promise<ReferenceImage> {
    const form = new FormData();
    form.append("file", file);
    return QuotesClient.toImage(
      await this.http.upload<ReferenceImagePayload>(`/quotes/${quoteId}/reference-images`, form),
    );
  }

  async removeImage(quoteId: string, imageId: string): Promise<void> {
    await this.http.delete(`/quotes/${quoteId}/reference-images/${imageId}`);
  }

  private static toPayload(fields: QuoteFields): Record<string, unknown> {
    return {
      origin: fields.origin,
      description: fields.description,
      body_region: fields.bodyRegion,
      size_estimate: fields.sizeEstimate,
      total_value: fields.totalValue,
      planned_sessions: fields.plannedSessions,
      planned_value_per_session: fields.plannedValuePerSession,
      estimated_duration_minutes: fields.estimatedDurationMinutes,
      notes: fields.notes,
    };
  }

  private static toQuote(payload: QuotePayload): Quote {
    return {
      id: payload.id,
      clientId: payload.client_id,
      artistId: payload.artist_id,
      origin: payload.origin as QuoteOrigin,
      description: payload.description,
      bodyRegion: payload.body_region,
      sizeEstimate: payload.size_estimate,
      totalValue: payload.total_value,
      plannedSessions: payload.planned_sessions,
      plannedValuePerSession: payload.planned_value_per_session,
      estimatedDurationMinutes: payload.estimated_duration_minutes,
      notes: payload.notes,
      status: payload.status as QuoteStatus,
      artistPercentage: payload.artist_percentage,
      approvedAt: payload.approved_at,
      rejectionReason: payload.rejection_reason,
      rejectionNote: payload.rejection_note,
      createdAt: payload.created_at,
    };
  }

  private static toImage(payload: ReferenceImagePayload): ReferenceImage {
    return {
      id: payload.id,
      contentType: payload.content_type,
      byteSize: payload.byte_size,
      uploadedAt: payload.uploaded_at,
      contentPath: payload.content_path,
    };
  }
}
