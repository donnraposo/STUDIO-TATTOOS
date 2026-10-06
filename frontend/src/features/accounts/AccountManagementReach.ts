import type { AuthenticatedUser, UserRole } from "@/shared/domain/AuthenticatedUser";
import type { StudioAccount } from "@/shared/domain/StudioAccount";

/** Até onde a alçada de quem está olhando alcança (RN 2.2, 2.5 e 2.6).
 *
 * Espelha o `AccountManagementPolicy` do backend: o proprietário administra
 * todo mundo, o gerente administra residentes e guests, e ninguém mais
 * administra ninguém. **É aparência, não garantia** — quem recusa de verdade é
 * o servidor, com 403.
 *
 * Fica separada do `ProfilePermissions` porque a pergunta é de outra natureza:
 * lá se pergunta o que um perfil vê, e a resposta depende de uma pessoa; aqui
 * se pergunta se uma pessoa alcança outra, e a resposta depende de duas. Juntar
 * as duas num lugar faria o `ProfilePermissions` receber um segundo argumento
 * que quase nenhum método dele usa.
 *
 * **Ninguém se bloqueia.** O backend também impede que o último proprietário
 * ativo seja bloqueado; aquela recusa é dele, porque depende de contar contas e
 * esta classe não consulta nada.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class AccountManagementReach {
  private static readonly MANAGEABLE_BY_MANAGER: UserRole[] = ["RESIDENT", "GUEST"];
  private static readonly CREATABLE_BY_OWNER: UserRole[] = [
    "OWNER",
    "MANAGER",
    "RESIDENT",
    "GUEST",
  ];

  /** Criar uma conta com este papel. O gerente não cria gerente nem
   * proprietário (RN 2.2): isso seria promover a si mesmo por tabela. */
  canCreate(actor: AuthenticatedUser, role: UserRole): boolean {
    return this.creatableRoles(actor).includes(role);
  }

  creatableRoles(actor: AuthenticatedUser): UserRole[] {
    if (actor.role === "OWNER") {
      return AccountManagementReach.CREATABLE_BY_OWNER;
    }
    if (actor.role === "MANAGER") {
      return AccountManagementReach.MANAGEABLE_BY_MANAGER;
    }
    return [];
  }

  /** Corrigir o cadastro (RN 2.6).
   *
   * **A própria conta entra**, ao contrário do bloqueio: corrigir o próprio
   * telefone não tem consequência nenhuma, e proibi-lo obrigaria o
   * proprietário a pedir a outra pessoa que arrume o nome dele. */
  canEdit(actor: AuthenticatedUser, account: StudioAccount): boolean {
    if (actor.role === "OWNER") {
      return true;
    }
    if (actor.role === "MANAGER") {
      return AccountManagementReach.MANAGEABLE_BY_MANAGER.includes(account.role);
    }
    return false;
  }

  /** Trocar o perfil de uma conta.
   *
   * **Só o proprietário, e é literal:** a RN 2.6 diz que o gerente não pode
   * promover usuários *"nem alterar perfis de acesso"* — as duas coisas. Trocar
   * residente por guest também é alterar perfil: muda a exigência de sinal
   * (RN-GST-004) e o repasse de quem o estúdio indica. */
  canChangeRole(actor: AuthenticatedUser): boolean {
    return actor.role === "OWNER";
  }

  /** Bloquear e desbloquear. A própria conta fica de fora: quem se bloqueia
   * perde a sessão no mesmo instante e não tem como voltar. */
  canChangeStatus(actor: AuthenticatedUser, account: StudioAccount): boolean {
    if (actor.id === account.id) {
      return false;
    }
    if (actor.role === "OWNER") {
      return true;
    }
    if (actor.role === "MANAGER") {
      return AccountManagementReach.MANAGEABLE_BY_MANAGER.includes(account.role);
    }
    return false;
  }

  /** Alterar o acordo de percentual.
   *
   * Basta ser gestão, e é assim no backend (`SetArtistPercentage` exige apenas
   * `is_staff`): a RN-CLI-003 reserva o percentual à gestão sem distinguir
   * gerente de proprietário. Mais estrito aqui esconderia um botão que o
   * servidor aceitaria. */
  canSetShare(actor: AuthenticatedUser, account: StudioAccount): boolean {
    return ["OWNER", "MANAGER"].includes(actor.role) && account.tattoos;
  }
}
