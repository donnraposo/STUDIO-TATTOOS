import type { BadgeTone } from "@/shared/components/StatusBadge.vue";
import { StudioSplit } from "@/shared/domain/StudioSplit";
import type { QuoteOrigin, QuoteStatus } from "@/shared/domain/Quote";

export interface StatusLook {
  label: string;
  tone: BadgeTone;
}

/** Como um orçamento se apresenta na tela.
 *
 * Três mapas tipados num lugar só, em vez de espalhados pelos componentes que
 * precisam deles. A lista, o detalhe e o formulário mostram o mesmo estado e a
 * mesma origem; se cada um trouxesse o próprio mapa, bastaria acrescentar um
 * estado para que um deles passasse a exibir o nome cru da API.
 *
 * Classe pura: não conhece a API, a sessão, nem o Vue. Testável sem montar
 * tela, como manda a convenção do frontend. */
export class QuoteDisplay {
  private static readonly STATUS: Record<QuoteStatus, StatusLook> = {
    PENDING: { label: "Pending", tone: "warning" },
    APPROVED: { label: "Approved", tone: "positive" },
    REJECTED: { label: "Rejected", tone: "danger" },
  };

  private static readonly ORIGIN: Record<QuoteOrigin, string> = {
    ARTIST_OWN: "Artist's own client",
    STUDIO_REFERRAL: "Studio referral",
  };

  /** A divisão mora no `StudioSplit`, e não aqui: ela é a mesma no formulário
   * de agendamento, no acordo por artista e nesta tela, e três cópias
   * divergiriam na primeira renegociação. */
  private static readonly SPLIT = new StudioSplit();

  status(status: QuoteStatus): StatusLook {
    return QuoteDisplay.STATUS[status];
  }

  origin(origin: QuoteOrigin): string {
    return QuoteDisplay.ORIGIN[origin];
  }

  standardPercentage(origin: QuoteOrigin): string {
    return QuoteDisplay.SPLIT.artistShareFor(origin);
  }

  /** As origens na ordem em que o formulário as oferece. */
  origins(): QuoteOrigin[] {
    return Object.keys(QuoteDisplay.ORIGIN) as QuoteOrigin[];
  }
}
