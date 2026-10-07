import type { AuthenticatedUser, UserRole } from "@/shared/domain/AuthenticatedUser";
import { HttpClient } from "@/shared/api/HttpClient";

/** Forma exata em que a API responde a identidade, em `snake_case`.
 *
 * Fica confinada a este arquivo de propósito: é a única parte da interface que
 * precisa conhecer a convenção de nomes do backend. */
interface CurrentUserPayload {
  id: string;
  email: string;
  full_name: string;
  role: string;
  acts_as_artist: boolean;
}

/** Entrada, saída e identidade da sessão (`/auth/*`).
 *
 * Nenhum dos três guarda estado: quem mantém a sessão viva na interface é o
 * `SessionStore`. Este cliente só sabe falar com a API. */
export class AuthClient {
  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  /** Entra e devolve quem entrou.
   *
   * São duas chamadas porque `POST /auth/login` responde apenas um status: ele
   * estabelece a sessão por cookie e não descreve o usuário. Toda pessoa que
   * chamasse `login` precisaria emendar `currentUser` em seguida, então a
   * emenda fica aqui, uma vez. */
  async login(email: string, password: string): Promise<AuthenticatedUser> {
    await this.http.post<Record<string, string>>("/auth/login", { email, password });
    return this.currentUser();
  }

  /** Identidade da sessão corrente. Responde 401 quando não há sessão válida,
   * e é isso que a guarda de rota usa para decidir. */
  async currentUser(): Promise<AuthenticatedUser> {
    return AuthClient.toUser(await this.http.get<CurrentUserPayload>("/auth/me"));
  }

  async logout(): Promise<void> {
    await this.http.post<null>("/auth/logout");
  }

  private static toUser(payload: CurrentUserPayload): AuthenticatedUser {
    return {
      id: payload.id,
      email: payload.email,
      fullName: payload.full_name,
      role: payload.role as UserRole,
      actsAsArtist: payload.acts_as_artist,
    };
  }
}
