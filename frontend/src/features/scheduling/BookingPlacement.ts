import { StudioClock } from "@/shared/format/StudioClock";

/** Onde um agendamento cai na grade da timeline.
 *
 * `column` e `span` são coordenadas de CSS Grid, contadas a partir de 1 na
 * primeira faixa de horário. */
export interface Placement {
  column: number;
  span: number;
  /** Verdadeiro quando o agendamento começa antes da abertura ou termina
   * depois do fechamento, e o bloco foi aparado para caber. A tela usa isso
   * para sinalizar que há mais sessão fora da vista. */
  clipped: boolean;
}

/** Converte horário em coordenada de grade.
 *
 * **Classe pura, separada do componente de propósito.** Esta aritmética é o que
 * tem chance real de estar errado — minutos desde a abertura, largura
 * proporcional, virada do horário de verão — e testá-la aqui não exige montar
 * tela nenhuma. Dentro do componente, ela seria testada pela aparência, ou não
 * seria testada.
 *
 * Todos os horários são lidos no fuso do estúdio, nunca no do navegador: um
 * artista consultando de outro país precisa ver a agenda de Cork.
 *
 * O bloco é **aparado** nas bordas em vez de descartado. Uma sessão que começou
 * às 9h30 e entra pelo expediente existe e ocupa a maca; sumir da tela porque
 * começou cedo demais seria esconder ocupação real. */
export class BookingPlacement {
  private readonly clock: StudioClock;
  private readonly openingMinutes: number;
  private readonly closingMinutes: number;
  private readonly slotMinutes: number;

  constructor(
    openingHour: number,
    closingHour: number,
    slotMinutes: number,
    clock: StudioClock = new StudioClock(),
  ) {
    this.clock = clock;
    this.openingMinutes = openingHour * 60;
    this.closingMinutes = closingHour * 60;
    this.slotMinutes = slotMinutes;
  }

  /** Quantas faixas o dia tem. A grade se desenha a partir disto. */
  get slotCount(): number {
    return (this.closingMinutes - this.openingMinutes) / this.slotMinutes;
  }

  /** Rótulos de hora cheia, para o cabeçalho da grade. */
  get hourLabels(): string[] {
    const labels: string[] = [];
    for (let minutes = this.openingMinutes; minutes < this.closingMinutes; minutes += 60) {
      labels.push(`${String(Math.floor(minutes / 60)).padStart(2, "0")}:00`);
    }
    return labels;
  }

  /** `null` quando o agendamento não toca o expediente do dia. */
  place(startsAt: string, endsAt: string): Placement | null {
    const start = this.clock.minutesSinceMidnight(startsAt);
    const end = this.endMinutes(startsAt, endsAt);

    if (end <= this.openingMinutes || start >= this.closingMinutes) {
      return null;
    }

    const visibleStart = Math.max(start, this.openingMinutes);
    const visibleEnd = Math.min(end, this.closingMinutes);

    return {
      column: Math.floor((visibleStart - this.openingMinutes) / this.slotMinutes) + 1,
      span: Math.max(1, Math.ceil((visibleEnd - visibleStart) / this.slotMinutes)),
      clipped: start < this.openingMinutes || end > this.closingMinutes,
    };
  }

  /** Meia-noite lida como fim do dia, e não como início.
   *
   * Uma sessão que termina exatamente às 00:00 devolveria zero minutos, e o
   * bloco apareceria invertido — fim antes do começo. Tratar o fim como 24h
   * resolve o caso sem inventar aritmética de data. */
  private endMinutes(startsAt: string, endsAt: string): number {
    const end = this.clock.minutesSinceMidnight(endsAt);
    const start = this.clock.minutesSinceMidnight(startsAt);
    return end <= start ? 24 * 60 : end;
  }
}
