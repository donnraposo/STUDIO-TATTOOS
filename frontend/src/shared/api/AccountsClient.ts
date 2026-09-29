import { HttpClient } from "@/shared/api/HttpClient";
import type { UserRole } from "@/shared/domain/AuthenticatedUser";
import type { StudioMember } from "@/shared/domain/StudioMember";

interface AccountPayload {
  id: string;
  email: string;
  full_name: string;
  artist_name: string | null;
  phone: string;
  role: string;
  acts_as_artist: boolean;
  status: string;
}

/** Contas do estúdio (`/users`).
 *
 * **Só o gestor consegue listar** — o backend recusa os demais com 403. Quem
 * chama precisa tratar isso: um residente agenda para si mesmo e não precisa
 * da lista. */
export class AccountsClient {
  private static readonly ARTIST_ROLES = ["RESIDENT", "GUEST"];

  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  /** Quem pode receber um agendamento: contas ativas com agenda própria.
   *
   * Conta bloqueada fica de fora. Agendar para alguém sem acesso criaria um
   * compromisso que a própria pessoa não conseguiria ver (RN 2.5). */
  async listArtists(): Promise<StudioMember[]> {
    const payload = await this.http.get<AccountPayload[]>("/users");
    return payload
      .filter((account) => account.status === "ACTIVE" && AccountsClient.tattoos(account))
      .map(AccountsClient.toMember);
  }

  private static tattoos(account: AccountPayload): boolean {
    return AccountsClient.ARTIST_ROLES.includes(account.role) || account.acts_as_artist;
  }

  private static toMember(account: AccountPayload): StudioMember {
    return {
      id: account.id,
      displayName: account.artist_name ?? account.full_name,
      role: account.role as UserRole,
      tattoos: AccountsClient.tattoos(account),
    };
  }
}
