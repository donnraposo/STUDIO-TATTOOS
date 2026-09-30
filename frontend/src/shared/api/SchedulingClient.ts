import { ApiError } from "@/shared/api/ApiError";
import { HttpClient } from "@/shared/api/HttpClient";
import type {
  Booking,
  BookingConflict,
  BookingStatus,
  Booth,
  RejectionReason,
} from "@/shared/domain/Booking";

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

  /** As solicitações esperando decisão, **sem janela de data** (RN-AGE-012).
   *
   * É a exceção deliberada ao parágrafo acima. A tela de agenda sempre informa
   * um intervalo porque olha um dia; o painel pergunta outra coisa — o que está
   * parado — e uma solicitação esquecida é justamente a que ninguém foi
   * procurar no dia certo. O filtro por estado é o que mantém o conjunto
   * pequeno no lugar da janela. */
  async listPending(): Promise<Booking[]> {
    const payload = await this.http.get<BookingPayload[]>("/bookings?status=REQUESTED");
    return payload.map(SchedulingClient.toBooking);
  }

  /** Cria a reserva. Residente e guest criam em `REQUESTED`; o gestor pode
   * criar ja aprovada (RN-AGE-005).
   *
   * Nenhuma verificacao de conflito acontece antes: quem decide e a restricao
   * do banco, no momento da gravacao (ADR-011). Um 409 aqui e resposta
   * esperada, nao falha da interface. */
  async create(booking: {
    clientId: string;
    boothId: string;
    startsAt: string;
    endsAt: string;
    artistId: string | null;
    approveImmediately: boolean;
  }): Promise<Booking> {
    return SchedulingClient.toBooking(
      await this.http.post<BookingPayload>("/bookings", {
        client_id: booking.clientId,
        booth_id: booking.boothId,
        starts_at: booking.startsAt,
        ends_at: booking.endsAt,
        artist_id: booking.artistId,
        approve_immediately: booking.approveImmediately,
      }),
    );
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

  /** Cancelamento e nao comparecimento (RN-AGE-009 e RN-AGE-010).
   *
   * O mesmo endpoint atende aos dois, distinguidos por `noShow`. Sao estados
   * diferentes de proposito: cancelado e nao comparecido tem o mesmo efeito
   * sobre o sinal, mas so o segundo diz que o horario foi perdido com o cliente
   * ausente -- e isso pesa no historico dele. */
  async cancel(bookingId: string, reason: string, noShow: boolean): Promise<Booking> {
    return SchedulingClient.toBooking(
      await this.http.post<BookingPayload>(`/bookings/${bookingId}/cancel`, {
        reason,
        no_show: noShow,
      }),
    );
  }

  /** Remarcacao (RN-AGE-008). So o gestor efetiva, e a maca pode mudar junto.
   *
   * Pode responder 409 como qualquer gravacao de agenda: o novo intervalo passa
   * pelas mesmas restricoes do banco. */
  async reschedule(
    bookingId: string,
    startsAt: string,
    endsAt: string,
    boothId: string | null,
  ): Promise<Booking> {
    return SchedulingClient.toBooking(
      await this.http.post<BookingPayload>(`/bookings/${bookingId}/reschedule`, {
        starts_at: startsAt,
        ends_at: endsAt,
        booth_id: boothId,
      }),
    );
  }

  /** Lê o conflito de agenda de dentro de um erro, quando houver.
   *
   * Devolve `null` para qualquer outra falha, inclusive um 409 que venha sem os
   * campos — uma versão mais antiga da API, por exemplo. A tela precisa
   * distinguir "conflito com reserva conhecida" de "deu erro", porque só o
   * primeiro abre o modal da RN-AGE-007. */
  static conflictFrom(error: unknown): BookingConflict | null {
    if (!(error instanceof ApiError) || !error.isConflict) {
      return null;
    }

    const payload = error.payload as { scope?: unknown; conflicting_booking_id?: unknown } | null;
    if (payload?.scope !== "booth" && payload?.scope !== "artist") {
      return null;
    }

    return {
      scope: payload.scope,
      message: error.message,
      conflictingBookingId:
        typeof payload.conflicting_booking_id === "string"
          ? payload.conflicting_booking_id
          : null,
    };
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
