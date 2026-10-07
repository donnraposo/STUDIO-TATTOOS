import type { UserRole } from "@/shared/domain/AuthenticatedUser";

/** Quem tatua no estúdio (RN 2.3).
 *
 * Duas coisas dependem desta resposta, e nenhuma delas é cosmética: só quem
 * tatua tem agenda e repasse, e só quem tatua **precisa de nome de artista** —
 * o banco recusa o contrário em `ck_user_account_artist_name_required`.
 *
 * Classe própria porque a pergunta aparece em três lugares da interface: ao
 * mapear uma conta vinda da API, ao escolher o artista de um agendamento e ao
 * criar uma conta nova. Escrita em cada um deles, divergiria no primeiro perfil
 * novo — e a divergência seria silenciosa, porque cada tela continuaria
 * parecendo correta sozinha.
 *
 * Mora em `shared/domain` e não na pasta de contas por causa da direção das
 * dependências: o cliente de API precisa dela, e `shared` não importa de
 * `features`.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class ArtistRole {
  private static readonly ALWAYS: UserRole[] = ["RESIDENT", "GUEST"];

  /** O perfil tatua por definição. Residente e guest existem para atender, e
   * não há residente que não tatue — perguntar a eles se tatuam sugeriria que
   * existe. */
  isAlways(role: UserRole): boolean {
    return ArtistRole.ALWAYS.includes(role);
  }

  /** Quem tatua: o perfil de artista, ou a conta de gestão marcada como quem
   * também atende. O proprietário do estúdio atende, e sem a marca ele não
   * apareceria na agenda nem no repasse. */
  includes(role: UserRole, actsAsArtist: boolean): boolean {
    return this.isAlways(role) || actsAsArtist;
  }
}
