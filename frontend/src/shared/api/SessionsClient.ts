import { HttpClient } from "@/shared/api/HttpClient";
import type { SessionStatus, TattooSession } from "@/shared/domain/TattooSession";

interface SessionPayload {
  id: string;
  quote_id: string;
  sequence_number: number;
  status: string;
  origin: string;
  planned_value: string;
  charged_value: string | null;
  artist_percentage: string;
  performed_at: string | null;
  marked_done_by: string | null;
  confirmed_at: string | null;
  confirmed_by: string | null;
  created_at: string;
}

/** Sessões de tatuagem (`/sessions` e `/quotes/{id}/sessions`).
 *
 * **Não há criação.** As sessões nascem da aprovação do orçamento, na mesma
 * transação (RN-ORC-005): criar uma solta permitiria sessão sem orçamento
 * aprovado, que é o estado que a regra impede ao exigir que só sessão concluída
 * entre em repasse.
 *
 * A listagem pende do orçamento porque a sessão não existe fora dele; marcar e
 * confirmar pendem da sessão, porque quem age já a tem em mão. */
export class SessionsClient {
  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  async listForQuote(quoteId: string): Promise<TattooSession[]> {
    const payload = await this.http.get<SessionPayload[]>(`/quotes/${quoteId}/sessions`);
    return payload.map(SessionsClient.toSession);
  }

  /** O artista registra que a sessão aconteceu (RN-ORC-005 e RN-ORC-006).
   *
   * **Valor ausente significa sessão inteira.** A RN-ORC-006 só pede o valor
   * quando a sessão foi interrompida, e é ele que distingue uma coisa da outra.
   * Parcial precisa cobrar **menos** que o previsto — o servidor recusa o
   * contrário, porque aceitar o valor igual marcaria como interrompida uma
   * sessão que correu inteira. */
  async markPerformed(
    sessionId: string,
    chargedValue: string | null,
    performedAt: string | null = null,
  ): Promise<TattooSession> {
    return SessionsClient.toSession(
      await this.http.post<SessionPayload>(`/sessions/${sessionId}/mark-done`, {
        charged_value: chargedValue,
        performed_at: performedAt,
      }),
    );
  }

  /** O gestor confirma o valor recebido e a sessão fica concluída (RN-ORC-005).
   *
   * **Registra; não movimenta.** O recebimento acontece fora do sistema, e aqui
   * fica o registro de quem conferiu e quando. Valor diferente do informado pelo
   * artista exige motivo — correção silenciosa de valor é a diferença entre um
   * acerto e um desvio, e sem o motivo escrito nenhuma das duas se distingue da
   * outra. */
  async confirmPayment(
    sessionId: string,
    chargedValue: string | null,
    reason: string | null,
  ): Promise<TattooSession> {
    return SessionsClient.toSession(
      await this.http.post<SessionPayload>(`/sessions/${sessionId}/confirm-payment`, {
        charged_value: chargedValue,
        reason,
      }),
    );
  }

  /** O gestor refaz as sessões restantes depois de uma parcial (RN-ORC-006).
   *
   * Se a soma deixar de fechar com o valor aprovado, o orçamento volta a
   * Pendente e o percentual congelado é descartado. Quem chama precisa avisar
   * antes: quem ajusta uma sessão não espera perder a aprovação junto. */
  async adjustRemaining(quoteId: string, plannedValues: string[]): Promise<TattooSession[]> {
    const payload = await this.http.post<SessionPayload[]>(
      `/quotes/${quoteId}/sessions/adjust`,
      { planned_values: plannedValues },
    );
    return payload.map(SessionsClient.toSession);
  }

  private static toSession(payload: SessionPayload): TattooSession {
    return {
      id: payload.id,
      quoteId: payload.quote_id,
      sequenceNumber: payload.sequence_number,
      status: payload.status as SessionStatus,
      origin: payload.origin,
      plannedValue: payload.planned_value,
      chargedValue: payload.charged_value,
      artistPercentage: payload.artist_percentage,
      performedAt: payload.performed_at,
      markedDoneBy: payload.marked_done_by,
      confirmedAt: payload.confirmed_at,
      confirmedBy: payload.confirmed_by,
      createdAt: payload.created_at,
    };
  }
}
