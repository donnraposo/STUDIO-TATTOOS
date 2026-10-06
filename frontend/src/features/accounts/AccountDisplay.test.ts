import { describe, expect, it } from "vitest";

import { AccountDisplay } from "@/features/accounts/AccountDisplay";
import type { AccountStatus, StudioAccount } from "@/shared/domain/StudioAccount";

/** RN 2.1 a 2.6 e ADR-030. O que mais importa aqui é o acordo ausente: nulo
 * significa "segue a regra da origem", e a regra depende do atendimento — não
 * existe um número a mostrar, e `0%` diria ao artista que ele trabalha de
 * graça.
 */

function account(fields: Partial<StudioAccount> = {}): StudioAccount {
  return {
    id: "a1",
    email: "artist@studio.ie",
    fullName: "Ytalo Lyra",
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

describe("AccountDisplay", () => {
  const display = new AccountDisplay();

  it("names every role in plain English", () => {
    expect(display.role("OWNER")).toBe("Owner");
    expect(display.role("MANAGER")).toBe("Manager");
    expect(display.role("RESIDENT")).toBe("Resident artist");
    expect(display.role("GUEST")).toBe("Guest artist");
  });

  it("names every account state", () => {
    const named: AccountStatus[] = ["ACTIVE", "PENDING_APPROVAL", "BLOCKED", "REJECTED"];

    for (const status of named) {
      expect(display.status(status).label).not.toBe("");
    }
  });

  /** Bloqueada foi uma decisão do gestor; aguardando aprovação é um cadastro
   * que ninguém olhou ainda (RN 2.6). Vermelho nas duas esconderia que só uma
   * delas precisa de atenção. */
  it("separates a blocked account from one still waiting", () => {
    expect(display.status("BLOCKED").tone).toBe("danger");
    expect(display.status("PENDING_APPROVAL").tone).toBe("warning");
    expect(display.status("ACTIVE").tone).toBe("positive");
  });

  it("calls the person by their artist name when there is one", () => {
    expect(display.name(account({ artistName: "FARPA" }))).toBe("FARPA");
  });

  it("falls back to the civil name", () => {
    expect(display.name(account())).toBe("Ytalo Lyra");
  });

  it("shows an agreed share as a whole percentage", () => {
    expect(display.share(account({ defaultArtistPercentage: "85.00" }))).toBe("85%");
    expect(display.share(account({ defaultArtistPercentage: "70.00" }))).toBe("70%");
  });

  it("keeps a half percent that was actually agreed", () => {
    expect(display.share(account({ defaultArtistPercentage: "67.50" }))).toBe("67.5%");
  });

  /** O teste que mais importa deste arquivo. Sem acordo o artista fica em 70%
   * ou 50% conforme a origem do atendimento (RN-REP-001 e RN-REP-002), e por
   * isso não há um número único — mas há um dado, e a tela precisa dizê-lo. */
  it("says the artist follows the origin rule instead of showing zero", () => {
    const text = display.share(account({ defaultArtistPercentage: null }));

    expect(text).toBe("By origin");
    expect(text).not.toContain("0");
  });

  /** Texto que não é número não pode virar `NaN%` na tela: o gestor leria isso
   * como defeito do sistema, e a conta continua sem acordo de qualquer forma. */
  it("treats an unreadable share as no agreement", () => {
    expect(display.share(account({ defaultArtistPercentage: "abc" }))).toBe("By origin");
  });

  /** Só quem tatua tem repasse, e o backend recusa com 422 um percentual em
   * conta que não atende. */
  it("offers the share only where there is a payout to split", () => {
    expect(display.canSetShare(account({ tattoos: true }))).toBe(true);
    expect(display.canSetShare(account({ tattoos: false }))).toBe(false);
  });
});
