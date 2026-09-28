/** Perfis de acesso, espelhando `UserRole` do backend
 * (`01_REGRAS_DE_NEGOCIO.md` §2). */
export type UserRole = "OWNER" | "MANAGER" | "RESIDENT" | "GUEST";

/** O usuário da sessão, na forma que a interface usa.
 *
 * Os nomes são em `camelCase` enquanto a API responde em `snake_case`. A
 * tradução acontece uma vez, no `AuthClient`, e não espalhada pelas telas: se um
 * dia um campo for renomeado no backend, há um arquivo a mudar, não vinte. */
export interface AuthenticatedUser {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  actsAsArtist: boolean;
}
