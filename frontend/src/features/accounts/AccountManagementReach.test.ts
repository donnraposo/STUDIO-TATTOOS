import { describe, expect, it } from "vitest";

import { AccountManagementReach } from "@/features/accounts/AccountManagementReach";
import type { AuthenticatedUser, UserRole } from "@/shared/domain/AuthenticatedUser";
import type { StudioAccount } from "@/shared/domain/StudioAccount";

/** RN 2.2, 2.5 e 2.6. Espelho do `AccountManagementPolicy` do backend, e como
 * todo espelho pode divergir — é por isso que ele nunca decide sozinho nada que
 * importe: esconder um botão é cortesia, e quem recusa é o 403.
 */

function user(role: UserRole, id = "me"): AuthenticatedUser {
  return {
    id,
    email: "someone@studio.ie",
    fullName: "Someone",
    role,
    actsAsArtist: false,
  };
}

function account(fields: Partial<StudioAccount> = {}): StudioAccount {
  return {
    id: "a1",
    email: "artist@studio.ie",
    fullName: "Lisa",
    artistName: null,
    phone: "+353 87 111 1111",
    role: "RESIDENT",
    actsAsArtist: false,
    tattoos: true,
    status: "ACTIVE",
    defaultArtistPercentage: null,
    ...fields,
  };
}

describe("AccountManagementReach", () => {
  const reach = new AccountManagementReach();

  it("lets the owner create any role", () => {
    const owner = user("OWNER");

    expect(reach.canCreate(owner, "OWNER")).toBe(true);
    expect(reach.canCreate(owner, "MANAGER")).toBe(true);
    expect(reach.canCreate(owner, "RESIDENT")).toBe(true);
    expect(reach.canCreate(owner, "GUEST")).toBe(true);
  });

  /** RN 2.2: deixar o gerente criar gerente seria deixá-lo promover a si mesmo
   * por tabela — cria um par, pede ao par que o promova. */
  it("stops the manager from creating management accounts", () => {
    const manager = user("MANAGER");

    expect(reach.canCreate(manager, "RESIDENT")).toBe(true);
    expect(reach.canCreate(manager, "GUEST")).toBe(true);
    expect(reach.canCreate(manager, "MANAGER")).toBe(false);
    expect(reach.canCreate(manager, "OWNER")).toBe(false);
  });

  it("gives an artist nothing to create", () => {
    expect(reach.creatableRoles(user("RESIDENT"))).toEqual([]);
    expect(reach.creatableRoles(user("GUEST"))).toEqual([]);
  });

  it("lets the owner block anyone else", () => {
    expect(reach.canChangeStatus(user("OWNER"), account({ role: "MANAGER" }))).toBe(true);
    expect(reach.canChangeStatus(user("OWNER"), account({ role: "GUEST" }))).toBe(true);
  });

  /** RN 2.5: o gerente administra residentes e guests. Bloquear um
   * proprietário é coisa de proprietário. */
  it("stops the manager from blocking management", () => {
    const manager = user("MANAGER");

    expect(reach.canChangeStatus(manager, account({ role: "RESIDENT" }))).toBe(true);
    expect(reach.canChangeStatus(manager, account({ role: "MANAGER" }))).toBe(false);
    expect(reach.canChangeStatus(manager, account({ role: "OWNER" }))).toBe(false);
  });

  /** Quem se bloqueia perde a sessão no mesmo instante e não tem como voltar.
   * O botão some antes de o erro acontecer. */
  it("never offers the block button on your own account", () => {
    const owner = user("OWNER", "same");

    expect(reach.canChangeStatus(owner, account({ id: "same", role: "OWNER" }))).toBe(false);
  });

  it("gives an artist nobody to block", () => {
    expect(reach.canChangeStatus(user("RESIDENT"), account({ id: "other" }))).toBe(false);
  });

  /** O acordo de percentual é da gestão, sem distinguir gerente de
   * proprietário: é o que a RN-CLI-003 diz e o que o backend faz. Mais estrito
   * aqui esconderia um botão que o servidor aceitaria. */
  it("lets both management roles change an artist's share", () => {
    expect(reach.canSetShare(user("OWNER"), account())).toBe(true);
    expect(reach.canSetShare(user("MANAGER"), account())).toBe(true);
  });

  it("stops the artist from setting their own share", () => {
    const artist = user("RESIDENT", "a1");

    expect(reach.canSetShare(artist, account({ id: "a1" }))).toBe(false);
  });

  /** Conta que não atende não tem repasse, e um acordo nela nunca seria usado. */
  it("offers no share on an account that does not tattoo", () => {
    const nonArtist = account({ role: "MANAGER", tattoos: false });

    expect(reach.canSetShare(user("OWNER"), nonArtist)).toBe(false);
  });
});
