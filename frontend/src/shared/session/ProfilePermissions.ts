import type { AuthenticatedUser } from "@/shared/api/AuthenticatedUser";

/** O que cada perfil vê na interface.
 *
 * **Isto é aparência, não garantia.** Esconder um item de menu que o perfil não
 * pode usar é cortesia com quem olha a tela. Quem recusa de verdade é o
 * backend, que devolve 403 — e nenhuma tela pode assumir que, por ter
 * escondido a ação, ela está impedida.
 *
 * Espelha as políticas do backend: `QuotePolicy`, `SchedulingPolicy` e
 * `ClientVisibilityPolicy`. Como é cópia, pode divergir quando a regra mudar; é
 * por isso que ela nunca decide sozinha nada que importe.
 *
 * Métodos separados em vez de um mapa de perfil para lista de telas: a pergunta
 * que cada tela faz é diferente, e uma lista única esconderia que "decide" e
 * "vê tudo" não são a mesma coisa. */
export class ProfilePermissions {
  private static readonly STAFF_ROLES = ["OWNER", "MANAGER"];

  isStaff(user: AuthenticatedUser): boolean {
    return ProfilePermissions.STAFF_ROLES.includes(user.role);
  }

  /** Aprovar, recusar e decidir, na agenda e no orçamento. */
  canDecide(user: AuthenticatedUser): boolean {
    return this.isStaff(user);
  }

  /** RN-ORC-001: o guest não acessa orçamentos. A verificação é pelo perfil e
   * não por "atua como artista", porque o guest tatua e passaria. */
  canSeeQuotes(user: AuthenticatedUser): boolean {
    return this.isStaff(user) || user.role === "RESIDENT";
  }

  /** RN-GST-004: o guest informa os dados do cliente na reserva e não tem
   * cadastro de clientes. */
  canSeeClients(user: AuthenticatedUser): boolean {
    return this.isStaff(user) || user.role === "RESIDENT";
  }

  /** Gestão de contas é do gestor (RN 2.5 e 2.6). */
  canManageAccounts(user: AuthenticatedUser): boolean {
    return this.isStaff(user);
  }
}
