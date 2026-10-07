/** Estados do agendamento (RN-AGE-003).
 *
 * A separação entre `REQUESTED` e `APPROVED` é o que sustenta a RN-AGE-004:
 * pendente não bloqueia a maca para outro artista, mas já ocupa a agenda do
 * próprio artista. Na timeline, os dois precisam parecer diferentes. */
export type BookingStatus =
  | "REQUESTED"
  | "APPROVED"
  | "REJECTED"
  | "DONE"
  | "CANCELLED"
  | "NO_SHOW";

/** Motivos previstos para recusar (RN-AGE-006). Lista fechada: o motivo
 * alimenta o tratamento do sinal e os relatórios de cancelamento. */
export type RejectionReason = "SLOT_TAKEN" | "STUDIO_CLOSED" | "RESCHEDULED";

export interface Booking {
  id: string;
  clientId: string;
  artistId: string;
  benchId: string;
  startsAt: string;
  endsAt: string;
  status: BookingStatus;
  /** O trabalho orçado que este horário atende (migração 0011).
   *
   * Nulo é caso legítimo: o guest não acessa orçamentos (RN-ORC-001) e
   * agenda para clientes próprios sem nenhum. Não se confunde com a sessão,
   * que só existe depois da aprovação do orçamento. */
  quoteId: string | null;
  requestedAt: string;
  rejectionReason: string | null;
  rejectionNote: string | null;
}

/** Maca. Maca e bancada são um único recurso reservável (RN-AGE-001). */
export interface Bench {
  id: string;
  number: number;
  label: string | null;
  active: boolean;
}

/** O agendamento que já existia quando outro foi recusado por conflito.
 *
 * Vem no corpo do 409 e é o que alimenta o modal da RN-AGE-007 — aquele que
 * **não** oferece a opção de ignorar. */
export interface BookingConflict {
  scope: "bench" | "artist";
  message: string;
  conflictingBookingId: string | null;
}
