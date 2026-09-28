import { describe, expect, it } from "vitest";

import type { AuthenticatedUser, UserRole } from "@/shared/domain/AuthenticatedUser";
import { ProfilePermissions } from "@/shared/session/ProfilePermissions";

/** O que cada perfil enxerga na interface.
 *
 * **Isto testa aparência, não segurança.** A garantia é do backend, que recusa
 * com 403 e já tem a matriz coberta nos testes de permissão dele. O que se
 * verifica aqui é que o menu não oferece a alguém uma tela que ele receberia
 * recusada — oferecer e negar em seguida é pior do que não oferecer.
 *
 * O caso do guest é o que justifica o arquivo: ele **tatua**, então qualquer
 * verificação baseada em "atua como artista" o deixaria passar para os
 * orçamentos, que a RN-ORC-001 lhe nega. */
function userWith(role: UserRole, actsAsArtist = false): AuthenticatedUser {
  return {
    id: "1",
    email: `${role.toLowerCase()}@studio.ie`,
    fullName: "Studio Person",
    role,
    actsAsArtist,
  };
}

describe("ProfilePermissions", () => {
  const permissions = new ProfilePermissions();

  it.each([
    ["OWNER", true],
    ["MANAGER", true],
    ["RESIDENT", false],
    ["GUEST", false],
  ] as const)("treats %s as staff: %s", (role, expected) => {
    expect(permissions.isStaff(userWith(role))).toBe(expected);
  });

  it("keeps the guest out of quotes even though the guest tattoos", () => {
    expect(permissions.canSeeQuotes(userWith("GUEST", true))).toBe(false);
    expect(permissions.canSeeQuotes(userWith("RESIDENT"))).toBe(true);
  });

  it("keeps the guest out of the client register", () => {
    /** RN-GST-004: o guest informa os dados do cliente na reserva e não tem
     * cadastro próprio. */
    expect(permissions.canSeeClients(userWith("GUEST", true))).toBe(false);
  });

  it("does not promote an owner who also tattoos", () => {
    /** Proprietário e gerente podem atuar como tatuadores sem perder a alçada
     * administrativa, e sem ganhar outra: `actsAsArtist` não muda nada aqui. */
    expect(permissions.canDecide(userWith("OWNER", true))).toBe(true);
    expect(permissions.canDecide(userWith("RESIDENT", true))).toBe(false);
  });

  it("leaves account management to the studio management", () => {
    expect(permissions.canManageAccounts(userWith("MANAGER"))).toBe(true);
    expect(permissions.canManageAccounts(userWith("RESIDENT"))).toBe(false);
  });
});
