import { ApiError } from "@/shared/api/ApiError";
import { CookieReader } from "@/shared/api/CookieReader";

/** A única costura entre a interface e a rede.
 *
 * Tudo o que toda chamada precisa mora aqui: envio do cookie de sessão, token
 * CSRF no cabeçalho pelo duplo envio, e tradução de resposta de erro em
 * `ApiError`. Se cada tela repetisse isso, bastaria uma esquecer o 401 para o
 * usuário ver uma tela quebrada em vez de voltar ao login.
 *
 * `credentials: "include"` é obrigatório: a sessão é cookie `HttpOnly` e o
 * `fetch` não o envia por padrão em requisição originada por script.
 *
 * O token CSRF só acompanha métodos que alteram estado. Em `GET` ele seria
 * ruído — e o backend não o exige ali. */
export class HttpClient {
  private static readonly CSRF_COOKIE = "studio_csrf";
  private static readonly CSRF_HEADER = "X-CSRF-Token";
  private static readonly SAFE_METHODS = ["GET", "HEAD"];

  private readonly baseUrl: string;
  private readonly cookies: CookieReader;
  private onUnauthenticated: (() => void) | null = null;

  constructor(baseUrl = "/api/v1", cookies: CookieReader = new CookieReader()) {
    this.baseUrl = baseUrl;
    this.cookies = cookies;
  }

  /** Registra o que fazer quando **qualquer** chamada responder 401.
   *
   * A sessão pode cair no meio do uso, por expiração ou porque a conta foi
   * bloqueada (RN 2.5) — e o backend reconfere a conta a cada requisição, então
   * isso acontece de verdade. Sem um ponto único, cada tela precisaria tratar o
   * caso, e bastaria uma esquecer para o usuário ficar olhando um erro genérico
   * numa tela que nunca mais vai carregar.
   *
   * Recebe uma função em vez de conhecer o roteador: quem sabe navegar é a
   * camada de aplicação, não o cliente HTTP. */
  whenUnauthenticated(handler: () => void): void {
    this.onUnauthenticated = handler;
  }

  async get<T>(path: string): Promise<T> {
    return this.send<T>("GET", path);
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    return this.send<T>("POST", path, body);
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    return this.send<T>("PUT", path, body);
  }

  async delete(path: string): Promise<void> {
    await this.send<void>("DELETE", path);
  }

  /** Envio de arquivo. Sem `Content-Type` manual de propósito: o navegador
   * precisa gerar o cabeçalho com a fronteira do multipart, e defini-lo à mão
   * produz um corpo que o servidor não consegue separar. */
  async upload<T>(path: string, form: FormData): Promise<T> {
    return this.request<T>("POST", path, form, {});
  }

  private async send<T>(method: string, path: string, body?: unknown): Promise<T> {
    const hasBody = body !== undefined;
    return this.request<T>(
      method,
      path,
      hasBody ? JSON.stringify(body) : undefined,
      hasBody ? { "Content-Type": "application/json" } : {},
    );
  }

  private async request<T>(
    method: string,
    path: string,
    body: BodyInit | undefined,
    headers: Record<string, string>,
  ): Promise<T> {
    const response = await globalThis.fetch(`${this.baseUrl}${path}`, {
      method,
      body,
      credentials: "include",
      headers: { ...headers, ...this.protectionHeaders(method) },
    });

    if (!response.ok) {
      const failure = await this.asApiError(response);
      if (failure.isUnauthenticated) {
        this.onUnauthenticated?.();
      }
      throw failure;
    }

    return (await this.readBody(response)) as T;
  }

  private protectionHeaders(method: string): Record<string, string> {
    if (HttpClient.SAFE_METHODS.includes(method)) {
      return {};
    }

    const token = this.cookies.read(HttpClient.CSRF_COOKIE);
    return token ? { [HttpClient.CSRF_HEADER]: token } : {};
  }

  /** `204` e corpo vazio não são erro: `DELETE` responde assim. */
  private async readBody(response: Response): Promise<unknown> {
    if (response.status === 204) {
      return null;
    }

    const text = await response.text();
    return text ? JSON.parse(text) : null;
  }

  /** Traduz a falha sem nunca deixar escapar um erro de análise.
   *
   * Uma resposta de erro pode não ser JSON — um proxy devolvendo HTML em 502,
   * por exemplo. Se a análise estourasse aqui, a tela receberia um
   * `SyntaxError` no lugar do problema real, que era a API fora do ar. */
  private async asApiError(response: Response): Promise<ApiError> {
    let detail = `Request failed with status ${response.status}.`;
    let payload: unknown = null;

    try {
      payload = JSON.parse(await response.text());
      detail = HttpClient.describe((payload as { detail?: unknown })?.detail) ?? detail;
    } catch {
      payload = null;
    }

    return new ApiError(response.status, detail, payload);
  }

  /** O backend fala de duas formas em `detail`, e ambas chegam aqui.
   *
   * Erro de domínio traduzido pelo `ErrorHandlers` vem como texto. Erro de
   * validação do Pydantic vem como lista de objetos com `msg`. Tratar só o
   * primeiro caso faria todo formulário recusado mostrar "Request failed with
   * status 422", escondendo justamente o campo que está errado. */
  private static describe(detail: unknown): string | null {
    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((entry) => (entry as { msg?: unknown })?.msg)
        .filter((message): message is string => typeof message === "string");
      return messages.length > 0 ? messages.join(" ") : null;
    }

    return null;
  }
}
