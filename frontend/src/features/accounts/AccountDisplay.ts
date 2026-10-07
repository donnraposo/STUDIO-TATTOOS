import type { BadgeTone } from "@/shared/components/StatusBadge.vue";
import type { UserRole } from "@/shared/domain/AuthenticatedUser";
import type { AccountStatus, StudioAccount } from "@/shared/domain/StudioAccount";
import { StudioSplit } from "@/shared/domain/StudioSplit";

export interface AccountLook {
  label: string;
  tone: BadgeTone;
}

/** Como uma conta se apresenta na área de gerenciamento (RN 2.1 a 2.6).
 *
 * Mapas tipados num lugar só, como em `PayoutDisplay`. A lista, o formulário e
 * o modal de bloqueio falam do mesmo papel e do mesmo estado; cada um com o seu
 * mapa passaria a exibir `PENDING_APPROVAL` cru no primeiro estado novo.
 *
 * **`BLOCKED` é perigo e `PENDING_APPROVAL` é espera.** São coisas diferentes:
 * a primeira foi uma decisão do gestor, a segunda é um cadastro que ninguém
 * olhou ainda (RN 2.6). Pintar as duas de vermelho esconderia que uma delas só
 * precisa de atenção.
 *
 * **O acordo nulo não é zero.** Nulo quer dizer que o artista segue a regra da
 * origem, e a regra depende do atendimento — 70% para cliente próprio, 50% para
 * indicação (RN-REP-001 e RN-REP-002). Não há um número único a mostrar, e
 * escrever `0%` diria ao artista que ele trabalha de graça. A tabela mostra
 * "By origin" e explica a frase uma vez, abaixo dela.
 *
 * Classe pura: não conhece API, sessão nem Vue. */
export class AccountDisplay {
  /** A conta dos dois lados mora num lugar só: esta tela, o formulário de
   * agendamento e o painel do trabalho fazem a mesma pergunta. */
  private static readonly SPLIT = new StudioSplit();

  private static readonly ROLE: Record<UserRole, string> = {
    OWNER: "Owner",
    MANAGER: "Manager",
    RESIDENT: "Resident artist",
    GUEST: "Guest artist",
  };

  private static readonly STATUS: Record<AccountStatus, AccountLook> = {
    ACTIVE: { label: "Active", tone: "positive" },
    PENDING_APPROVAL: { label: "Awaiting approval", tone: "warning" },
    BLOCKED: { label: "Blocked", tone: "danger" },
    REJECTED: { label: "Rejected", tone: "neutral" },
  };

  /** Texto exibido quando a conta não tem acordo próprio. */
  static readonly BY_ORIGIN = "By origin";

  role(role: UserRole): string {
    return AccountDisplay.ROLE[role];
  }

  status(status: AccountStatus): AccountLook {
    return AccountDisplay.STATUS[status];
  }

  /** O nome de artista quando existe, e o nome civil quando não.
   *
   * É o nome pelo qual o estúdio chama a pessoa, e é o que o gestor procura ao
   * percorrer a lista. */
  name(account: StudioAccount): string {
    return account.artistName ?? account.fullName;
  }

  /** O acordo, ou a ausência dele. Percentual inteiro: `85.00` vira `85%`,
   * porque duas casas num número que é sempre redondo só acrescentam ruído. */
  share(account: StudioAccount): string {
    const agreed = account.defaultArtistPercentage;
    if (agreed === null) {
      return AccountDisplay.BY_ORIGIN;
    }

    const parsed = Number(agreed);
    return Number.isFinite(parsed) ? `${Number(parsed.toFixed(2))}%` : AccountDisplay.BY_ORIGIN;
  }

  /** O que sobra para o estúdio, dado o percentual do artista.
   *
   * **Existe porque o estúdio pensa pelo outro lado.** Os acordos são ditos
   * como "30% se o cliente foi trazido pelo tatuador, 50% se foi indicação do
   * estúdio, 15% em condições especiais" — e esses são os percentuais **da
   * casa**. O sistema grava o do artista, que é o complemento: 70, 50 e 85.
   *
   * Mostrar os dois lados ao mesmo tempo é o que impede o erro que custaria
   * caro: digitar 30 querendo dizer "a casa fica com 30" e entregar 30% ao
   * artista. */
  studioShareOf(percentage: string): string {
    return AccountDisplay.SPLIT.studioShareOf(percentage);
  }

  /** Só quem tatua tem repasse, e só quem tem repasse tem acordo de percentual.
   *
   * O backend recusa com 422 um percentual em conta que não atende; esconder o
   * botão poupa o gestor de descobrir isso pelo erro. */
  canSetShare(account: StudioAccount): boolean {
    return account.tattoos;
  }
}
