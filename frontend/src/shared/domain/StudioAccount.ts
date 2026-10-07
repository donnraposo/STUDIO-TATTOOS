import type { UserRole } from "@/shared/domain/AuthenticatedUser";

/** Estados da conta, espelhando `UserStatus` do backend
 * (`01_REGRAS_DE_NEGOCIO.md` §2.5 e §2.6).
 *
 * `BLOCKED` preserva o histórico e encerra as sessões; não há exclusão de
 * conta, porque apagar quem assinou um atendimento apagaria o atendimento. */
export type AccountStatus = "PENDING_APPROVAL" | "ACTIVE" | "BLOCKED" | "REJECTED";

/** Uma conta do estúdio, na forma que a área de gerenciamento usa.
 *
 * Mais larga que o `StudioMember`, que carrega só o necessário para escolher um
 * artista numa lista. Aqui o gestor precisa ver papel, acesso e acordo — e por
 * isso são dois tipos, e não um com metade dos campos opcionais.
 *
 * `tattoos` chega **derivado**: a regra de quem tatua — perfil de artista ou
 * conta de gestão que também atende — mora no `AccountsClient`, uma vez, e não
 * é recalculada em cada tela que precisa dela.
 *
 * `defaultArtistPercentage` é **texto**, como todo decimal que vem da API, e
 * **nulo tem significado**: a conta segue a regra da origem — 70% para cliente
 * próprio, 50% para indicação do estúdio (ADR-030). Nulo não é zero, e a tela
 * não pode exibi-lo como tal. */
export interface StudioAccount {
  id: string;
  email: string;
  fullName: string;
  artistName: string | null;
  phone: string;
  role: UserRole;
  actsAsArtist: boolean;
  tattoos: boolean;
  status: AccountStatus;
  defaultArtistPercentage: string | null;
}
