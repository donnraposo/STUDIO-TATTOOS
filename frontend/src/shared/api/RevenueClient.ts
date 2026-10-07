import { HttpClient } from "@/shared/api/HttpClient";
import type {
  MonthlyRevenue,
  RevenueLine,
  RevenueReport,
  RevenueTotals,
} from "@/shared/domain/Revenue";

interface TotalsPayload {
  sessions: number;
  value: string;
  artists: string;
  studio: string;
}

interface LinePayload {
  session_id: string;
  artist_id: string;
  settled_at: string;
  value: string;
  percentage: string;
  artist_amount: string;
  studio_amount: string;
  transferred: boolean;
}

/** Faturamento do estúdio (`/revenue`).
 *
 * **Só leitura, porque só existe leitura.** Não há rota de escrita: um
 * relatório que corrigisse dado ao passar seria um relatório que muda o
 * passado, e a correção entra onde o fato aconteceu (RN-PAG-007).
 *
 * **Só gerente e proprietário** — o backend recusa os demais com 403 (RN 10.4).
 * O artista vê o que lhe diz respeito na tela de repasses, com o recorte dele. */
export class RevenueClient {
  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  async month(year: number, month: number): Promise<RevenueReport> {
    const payload = await this.http.get<{
      year: number;
      month: number;
      lines: LinePayload[];
      totals: TotalsPayload;
    }>(`/revenue?year=${year}&month=${month}`);

    return {
      year: payload.year,
      month: payload.month,
      lines: payload.lines.map(RevenueClient.toLine),
      totals: RevenueClient.toTotals(payload.totals),
    };
  }

  /** Os `count` meses que terminam no pedido, do mais antigo ao mais novo. */
  async monthly(year: number, month: number, count = 12): Promise<MonthlyRevenue[]> {
    const payload = await this.http.get<
      { year: number; month: number; totals: TotalsPayload }[]
    >(`/revenue/monthly?year=${year}&month=${month}&count=${count}`);

    return payload.map((each) => ({
      year: each.year,
      month: each.month,
      totals: RevenueClient.toTotals(each.totals),
    }));
  }

  private static toLine(payload: LinePayload): RevenueLine {
    return {
      sessionId: payload.session_id,
      artistId: payload.artist_id,
      settledAt: payload.settled_at,
      value: payload.value,
      percentage: payload.percentage,
      artistAmount: payload.artist_amount,
      studioAmount: payload.studio_amount,
      transferred: payload.transferred,
    };
  }

  private static toTotals(payload: TotalsPayload): RevenueTotals {
    return {
      sessions: payload.sessions,
      value: payload.value,
      artists: payload.artists,
      studio: payload.studio,
    };
  }
}
