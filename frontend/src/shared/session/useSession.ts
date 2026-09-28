import { useApi } from "@/shared/api/useApi";
import { ProfilePermissions } from "@/shared/session/ProfilePermissions";
import { SessionStore } from "@/shared/session/SessionStore";

const store = new SessionStore(useApi().auth);
const permissions = new ProfilePermissions();

/** Acesso à sessão única da aplicação.
 *
 * A instância é criada uma vez, no carregamento do módulo, e compartilhada.
 * Criar uma por componente daria a cada tela uma sessão própria, e sair em uma
 * não afetaria as outras.
 *
 * Devolve também as permissões de exibição, porque quem pergunta "quem está
 * logado" quase sempre pergunta em seguida "o que essa pessoa vê". */
export function useSession(): { session: SessionStore; permissions: ProfilePermissions } {
  return { session: store, permissions };
}
