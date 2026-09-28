import { readonly, ref, type DeepReadonly, type Ref } from "vue";

import { AuthClient } from "@/shared/api/AuthClient";
import type { AuthenticatedUser } from "@/shared/api/AuthenticatedUser";

/** A sessão do usuário dentro da interface.
 *
 * Uma classe com estado reativo em vez de Pinia: o estado compartilhado do MVP
 * é este, e uma biblioteca inteira para guardar um usuário e um booleano seria
 * dependência sem contrapartida. Se a M7.2 mostrar estado compartilhado de
 * verdade, a decisão se revê ali, com motivo.
 *
 * O estado é exposto **somente para leitura**. Uma tela que pudesse escrever
 * `user` diretamente conseguiria simular um perfil que não é o seu e, pior,
 * deixaria a interface discordando do servidor sem que nada tivesse falhado.
 *
 * `restore` é o que sustenta recarregar a página: o cookie sobrevive ao
 * recarregamento, o estado em memória não. */
export class SessionStore {
  private readonly auth: AuthClient;
  private readonly currentUser = ref<AuthenticatedUser | null>(null);
  private readonly restoring = ref(true);

  constructor(auth: AuthClient = new AuthClient()) {
    this.auth = auth;
  }

  get user(): DeepReadonly<Ref<AuthenticatedUser | null>> {
    return readonly(this.currentUser);
  }

  /** Verdadeiro enquanto a sessão ainda não foi conferida com o servidor.
   *
   * A guarda de rota precisa disto: sem ele, o primeiro acesso a uma rota
   * protegida veria `user` nulo — porque a conferência ainda não voltou — e
   * mandaria ao login quem estava perfeitamente autenticado. */
  get isRestoring(): DeepReadonly<Ref<boolean>> {
    return readonly(this.restoring);
  }

  /** Reconhece a sessão existente a partir do cookie, sem nunca falhar.
   *
   * Qualquer erro vira "não autenticado, até onde a interface sabe": 401 é o
   * caso esperado, e API fora do ar ou rede caída levam ao mesmo lugar, a tela
   * de entrada. Propagar a falha daqui impediria a aplicação de montar, e uma
   * tela branca é resposta muito pior do que um formulário de login — que,
   * aliás, vai mostrar o erro real na primeira tentativa. */
  async restore(): Promise<void> {
    this.restoring.value = true;
    try {
      this.currentUser.value = await this.auth.currentUser();
    } catch {
      this.currentUser.value = null;
    } finally {
      this.restoring.value = false;
    }
  }

  async signIn(email: string, password: string): Promise<void> {
    this.currentUser.value = await this.auth.login(email, password);
  }

  /** Encerra no servidor e depois esquece localmente.
   *
   * A ordem importa: limpar antes e falhar a chamada deixaria a interface
   * achando que saiu enquanto a sessão continuaria válida no servidor — e um
   * "voltar" do navegador reabriria tudo. */
  async signOut(): Promise<void> {
    await this.auth.logout();
    this.currentUser.value = null;
  }

  /** Chamado quando qualquer requisição responde 401: a sessão caiu por
   * expiração ou porque a conta foi bloqueada (RN 2.5). */
  forget(): void {
    this.currentUser.value = null;
  }
}
