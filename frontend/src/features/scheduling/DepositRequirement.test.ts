import { describe, expect, it } from "vitest";

import { DepositRequirement } from "@/features/scheduling/DepositRequirement";
import type { StudioMember } from "@/shared/domain/StudioMember";

/** RN-PAG-001 e RN-GST-004. O backend recusa criar já aprovado onde há sinal a
 * confirmar (ADR-027); a tela usa isto para não oferecer o atalho e levar 403 —
 * um botão que o servidor recusa ensina a equipe a desconfiar dos botões.
 */

const ARTISTS: StudioMember[] = [
  { id: "r1", displayName: "Vera", role: "RESIDENT", tattoos: true },
  { id: "g1", displayName: "Nyx", role: "GUEST", tattoos: true },
  { id: "o1", displayName: "Aoife", role: "OWNER", tattoos: true },
];

describe("DepositRequirement", () => {
  const deposits = new DepositRequirement();

  it("requires a deposit for a resident", () => {
    expect(deposits.appliesTo("r1", ARTISTS)).toBe(true);
  });

  it("requires a deposit for an owner who tattoos", () => {
    expect(deposits.appliesTo("o1", ARTISTS)).toBe(true);
  });

  /** O guest recebe diretamente dos clientes próprios, e esses valores não
   * passam pelo estúdio. Um agendamento novo nunca nasce ligado a um orçamento,
   * então o perfil basta. */
  it("does not require one for a guest", () => {
    expect(deposits.appliesTo("g1", ARTISTS)).toBe(false);
  });

  it("requires one when the artist is left as myself", () => {
    /** Quem cria pela agenda com essa opção é o gestor, que não é guest. */
    expect(deposits.appliesTo("", ARTISTS)).toBe(true);
  });

  it("errs towards requiring one when the artist is unknown", () => {
    /** Não oferecer o atalho custa um clique; oferecê-lo custa um 403 e a
     * confiança de quem opera. */
    expect(deposits.appliesTo("quem?", ARTISTS)).toBe(true);
  });
});
