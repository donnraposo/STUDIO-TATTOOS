import type { StudioMember } from "@/shared/domain/StudioMember";

/** Se um horário novo vai exigir sinal de €50 (RN-PAG-001 e RN-GST-004).
 *
 * **É aparência, não garantia.** Quem decide é o backend, que recusa a criação
 * já aprovada quando há sinal a confirmar (ADR-027). A tela usa isto para não
 * oferecer um atalho que o servidor nega — oferecer e ser recusado ensina a
 * equipe a desconfiar dos próprios botões.
 *
 * A exceção é a do guest com cliente próprio: a RN-GST-004 diz que ele recebe
 * diretamente e que esses valores não passam pelo estúdio. Um agendamento novo
 * nunca nasce ligado a um orçamento, então basta olhar o perfil de quem vai
 * atender.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class DepositRequirement {
  /** `artistId` vazio significa "eu mesmo" — e quem cria pela tela de agenda
   * com essa opção é o gestor, que não é guest. */
  appliesTo(artistId: string, artists: StudioMember[]): boolean {
    if (artistId === "") {
      return true;
    }
    const artist = artists.find((candidate) => candidate.id === artistId);
    return artist?.role !== "GUEST";
  }
}
