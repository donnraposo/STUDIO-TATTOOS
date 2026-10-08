/** O que cada decisão faz com o dinheiro, na letra das regras de negócio.
 *
 * Existe porque quem clica precisa saber a consequência **antes** de clicar, e
 * porque essas frases não podem variar de tela para tela. Cancelar retém o
 * sinal mesmo com aviso; não comparecer retém e ainda tira o repasse do
 * artista; remarcar depende do prazo de 24 horas. Escritas de improviso em cada
 * modal, três versões da mesma regra apareceriam.
 *
 * Classe pura, sem Vue: é texto de regra, e não comportamento de tela.
 *
 * **Nada disso é executado pela interface.** O efeito financeiro pertence ao
 * módulo de pagamentos. Aqui a tela apenas informa o que a regra determina — e
 * dizer isso em voz alta é melhor do que deixar o gestor decidir sem saber.
 *
 * **A frase da aprovação dizia que o sinal não era registrado no sistema**, e
 * deixou de ser verdade na M7.2.3: o painel do sinal fica logo acima dela, no
 * mesmo modal. Um texto que contradiz o que está na tela ao lado é pior do que
 * texto nenhum — ensina a não ler nenhum dos dois.
 *
 * **As frases deixaram de dizer "€50" em 08/10/2026.** Cada artista cobra o seu
 * sinal, e o valor passou a ser dito ao marcar o horário. Um texto que promete
 * cinquenta euros a quem combinou oitenta erra justamente onde dói: no que o
 * cliente recebe de volta. */
export type BookingDecisionKind = "approve" | "reject" | "cancel" | "noShow" | "reschedule";

export class BookingConsequence {
  private static readonly TEXT: Record<BookingDecisionKind, string> = {
    approve:
      "The deposit has to be confirmed before the booking can be approved.",
    reject:
      "The studio returns the deposit when it is the studio that rejects the request.",
    cancel:
      "The studio keeps the deposit, even when the client gives 24 hours' notice. Anything paid above it is returned.",
    noShow:
      "The studio keeps the deposit and returns anything paid above it. The artist receives no payout for a session that did not happen.",
    reschedule:
      "With at least 24 hours' notice the deposit moves to the new time. Outside that the client loses it and pays a new deposit; anything above it is returned.",
  };

  describe(kind: BookingDecisionKind): string {
    return BookingConsequence.TEXT[kind];
  }
}
