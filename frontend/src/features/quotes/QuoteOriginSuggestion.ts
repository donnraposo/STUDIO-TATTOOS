import type { Client } from "@/shared/domain/Client";
import type { QuoteOrigin } from "@/shared/domain/Quote";

/** Qual origem o formulário de orçamento abre marcada (RN-CLI-002).
 *
 * A regra é literal: *"se o cliente retornar ao mesmo artista **que o trouxe**,
 * será considerado cliente próprio do artista. Se o cliente retornar ao estúdio
 * e for encaminhado a outro artista, o novo atendimento será considerado
 * indicação do estúdio."*
 *
 * **Sugere, não decide.** A mesma regra diz que a origem é determinada **em cada
 * atendimento**, e a RN-CLI-003 reserva a correção ao gestor. O formulário abre
 * com a resposta provável e quem orça confirma ou troca — um valor que não
 * pudesse ser trocado transformaria uma sugestão em sentença, e decidiria
 * repasse sem ninguém ter olhado.
 *
 * **Sem saber quem trouxe, sugere indicação do estúdio.** É o lado seguro: a
 * indicação paga 50% ao artista, e errar para esse lado significa pagar a menos
 * até alguém conferir, em vez de pagar a mais e precisar cobrar de volta. Os
 * cadastros anteriores à migração `0008` estão todos nesse caso.
 *
 * Classe pura: não conhece API, Vue nem sessão. */
export class QuoteOriginSuggestion {
  /** `artistId` é o artista **efetivo** do orçamento, já resolvido — quem
   * chama sabe se o formulário está orçando para si ou para outra pessoa. */
  for(client: Client | null, artistId: string | null): QuoteOrigin {
    if (!client || client.broughtByArtistId === null || artistId === null) {
      return "STUDIO_REFERRAL";
    }
    return client.broughtByArtistId === artistId ? "ARTIST_OWN" : "STUDIO_REFERRAL";
  }
}
