/** Erro devolvido pela API, já traduzido para a linguagem da interface.
 *
 * Existe para que nenhuma tela precise inspecionar `Response` nem adivinhar o
 * significado de um número. O `status` fica disponível para quem precisa
 * distinguir um caso — 409 abre o modal de conflito da agenda —, mas o caminho
 * comum é apenas mostrar `message`.
 *
 * A mensagem vem do backend, que já a escreve em inglês e voltada ao usuário
 * (`ErrorHandlers`, ADR-021). Reescrevê-la aqui criaria duas versões da mesma
 * explicação, que divergiriam na primeira mudança de regra. */
export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, message: string, payload: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }

  /** Sessão ausente ou expirada: quem trata devolve o usuário ao login. */
  get isUnauthenticated(): boolean {
    return this.status === 401;
  }

  /** Perfil sem permissão. Diferente de 401: entrar de novo não resolve. */
  get isForbidden(): boolean {
    return this.status === 403;
  }

  /** Conflito de agenda (RN-AGE-007). A tela abre o modal, sem opção de ignorar. */
  get isConflict(): boolean {
    return this.status === 409;
  }
}
