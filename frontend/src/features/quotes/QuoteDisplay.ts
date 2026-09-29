import type { BadgeTone } from "@/shared/components/StatusBadge.vue";
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

  /** Percentual padrão de cada origem (RN-REP-001 e RN-REP-002).
   *
   * **É informação, não decisão.** Serve para o gestor saber o que será
   * congelado antes de aprovar. Quem congela é o backend, e o número que vale
   * depois disso é o que vem na resposta — nunca este. Se os dois divergirem, a
   * tela está errada e o repasse continua certo. */
  private static readonly STANDARD_PERCENTAGE: Record<QuoteOrigin, string> = {
    ARTIST_OWN: "70",
    STUDIO_REFERRAL: "50",
  };

  status(status: QuoteStatus): StatusLook {
    return QuoteDisplay.STATUS[status];
  }

  origin(origin: QuoteOrigin): string {
    return QuoteDisplay.ORIGIN[origin];
  }

  standardPercentage(origin: QuoteOrigin): string {
    return QuoteDisplay.STANDARD_PERCENTAGE[origin];
  }

  /** As origens na ordem em que o formulário as oferece. */
  origins(): QuoteOrigin[] {
    return Object.keys(QuoteDisplay.ORIGIN) as QuoteOrigin[];
  }
}
