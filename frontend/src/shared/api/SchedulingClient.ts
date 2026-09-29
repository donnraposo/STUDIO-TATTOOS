import { HttpClient } from "@/shared/api/HttpClient";
import type { Booking, BookingStatus, Booth, RejectionReason } from "@/shared/domain/Booking";

interface BoothPayload {
  id: string;
  number: number;
  label: string | null;
  active: boolean;
}

interface BookingPayload {
  id: string;
  client_id: string;
  artist_id: string;
  booth_id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  requested_at: string;
  rejection_reason: string | null;
  rejection_note: string | null;
}

/** Macas e agenda (`/booths` e `/bookings`).
 *
 * Um cliente para os dois porque são um recurso só do ponto de vista da tela:
 * a timeline não existe sem as macas, e pedir as duas coisas a objetos
 * diferentes só espalharia a montagem da mesma página. */
export class SchedulingClient {
  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  async listBooths(): Promise<Booth[]> {
    return this.http.get<BoothPayload[]>("/booths");
  }

  /** Agendamentos que **tocam** o intervalo informado.
   *
   * O recorte é obrigatório aqui, embora a API aceite listar tudo: uma tela de
   * agenda que pede o histórico inteiro funciona no primeiro mês e fica lenta
   * no sexto, sem ninguém ter mudado nada. */
  async listBookings(startsAt: string, endsAt: string): Promise<Booking[]> {
    const query = new URLSearchParams({ starts_at: startsAt, ends_at: endsAt });
    const payload = await this.http.get<BookingPayload[]>(`/bookings?${query.toString()}`);
    return payload.map(SchedulingClient.toBooking);
  }

  async approve(bookingId: string): Promise<Booking> {
    return SchedulingClient.toBooking(
      await this.http.post<BookingPayload>(`/bookings/${bookingId}/approve`),
    );
  }

  async reject(bookingId: string, reason: RejectionReason, note: string | null): Promise<Booking> {
    return SchedulingClient.toBooking(
      await this.http.post<BookingPayload>(`/bookings/${bookingId}/reject`, { reason, note }),
    );
  }

  private static toBooking(payload: BookingPayload): Booking {
    return {
      id: payload.id,
      clientId: payload.client_id,
      artistId: payload.artist_id,
      boothId: payload.booth_id,
      startsAt: payload.starts_at,
      endsAt: payload.ends_at,
      status: payload.status as BookingStatus,
      requestedAt: payload.requested_at,
      rejectionReason: payload.rejection_reason,
      rejectionNote: payload.rejection_note,
    };
  }
}
