import { HttpClient } from "@/shared/api/HttpClient";
import { ArtistRole } from "@/shared/domain/ArtistRole";
import type { UserRole } from "@/shared/domain/AuthenticatedUser";
import type { AccountStatus, StudioAccount } from "@/shared/domain/StudioAccount";
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
  default_artist_percentage: string | null;
}

/** Dados de uma conta nova. Espelha `CreateAccountRequest` do backend. */
export interface NewAccount {
  email: string;
  password: string;
  fullName: string;
  phone: string;
  role: UserRole;
  actsAsArtist: boolean;
  artistName: string | null;
}

/** Contas do estúdio (`/users`).
 *
 * **Só o gestor consegue listar** — o backend recusa os demais com 403. Quem
 * chama precisa tratar isso: um residente agenda para si mesmo e não precisa
 * da lista.
 *
 * As duas leituras têm formas diferentes de propósito. `listArtists` devolve o
 * mínimo para preencher um seletor; `listAll` devolve a conta inteira, para a
 * área de gerenciamento. Uma só, com campos sobrando, faria toda tela carregar
 * acordo de percentual para desenhar um `<select>` de nomes.
 *
 * **Quem tatua desce derivado**, pelo `ArtistRole`, nos dois tipos. A regra
 * aparece em três lugares da interface; recalculada em cada tela, divergiria no
 * primeiro perfil novo. */
export class AccountsClient {
  private static readonly ARTIST = new ArtistRole();

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

  /** Todas as contas, incluindo as bloqueadas.
   *
   * Sem filtro: numa área de gerenciamento, esconder a conta bloqueada
   * esconderia justamente o botão que a desbloqueia. */
  async listAll(): Promise<StudioAccount[]> {
    const payload = await this.http.get<AccountPayload[]>("/users");
    return payload.map(AccountsClient.toAccount);
  }

  async create(account: NewAccount): Promise<StudioAccount> {
    const payload = await this.http.post<AccountPayload>("/users", {
      email: account.email,
      password: account.password,
      full_name: account.fullName,
      phone: account.phone,
      role: account.role,
      acts_as_artist: account.actsAsArtist,
      artist_name: account.artistName,
    });
    return AccountsClient.toAccount(payload);
  }

  /** O motivo é obrigatório (RN 2.5): o bloqueio precisa ficar rastreável. */
  async block(accountId: string, reason: string): Promise<void> {
    await this.http.post(`/users/${accountId}/block`, { reason });
  }

  async unblock(accountId: string): Promise<void> {
    await this.http.post(`/users/${accountId}/unblock`);
  }

  /** O acordo de percentual do artista (ADR-030).
   *
   * `PUT` com nulo **encerra** o acordo e devolve o artista à regra da origem.
   * O percentual vai como texto, do campo ao corpo da requisição, sem passar
   * por `number`: é a mesma razão pela qual o dinheiro não passa. */
  async setPercentage(accountId: string, percentage: string | null): Promise<StudioAccount> {
    const payload = await this.http.put<AccountPayload>(`/users/${accountId}/percentage`, {
      percentage,
    });
    return AccountsClient.toAccount(payload);
  }

  private static tattoos(account: AccountPayload): boolean {
    return AccountsClient.ARTIST.includes(account.role as UserRole, account.acts_as_artist);
  }

  private static toMember(account: AccountPayload): StudioMember {
    return {
      id: account.id,
      displayName: account.artist_name ?? account.full_name,
      role: account.role as UserRole,
      tattoos: AccountsClient.tattoos(account),
    };
  }

  private static toAccount(account: AccountPayload): StudioAccount {
    return {
      id: account.id,
      email: account.email,
      fullName: account.full_name,
      artistName: account.artist_name,
      phone: account.phone,
      role: account.role as UserRole,
      actsAsArtist: account.acts_as_artist,
      tattoos: AccountsClient.tattoos(account),
      status: account.status as AccountStatus,
      defaultArtistPercentage: account.default_artist_percentage,
    };
  }
}
