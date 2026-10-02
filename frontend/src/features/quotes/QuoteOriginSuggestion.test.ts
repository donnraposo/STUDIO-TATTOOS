import { describe, expect, it } from "vitest";

import { QuoteOriginSuggestion } from "@/features/quotes/QuoteOriginSuggestion";
import type { Client } from "@/shared/domain/Client";

/** RN-CLI-002: a origem decide o dinheiro — 70% para cliente próprio, 50% para
 * indicação do estúdio. A sugestão é o que evita o caminho preguiçoso de abrir
 * sempre em "cliente próprio" e deixar o descuido pagar a mais.
 */

function client(overrides: Partial<Client> = {}): Client {
  return {
    id: "c1",
    name: "Niamh",
    phone: "+353 87 111 1111",
    instagram: null,
    registeredByArtistId: "a1",
    broughtByArtistId: "a1",
    createdAt: "2026-09-01T10:00:00+01:00",
    ...overrides,
  };
}

describe("QuoteOriginSuggestion", () => {
  const suggestion = new QuoteOriginSuggestion();

  it("recognises the artist who brought the client", () => {
    expect(suggestion.for(client(), "a1")).toBe("ARTIST_OWN");
  });

  it("treats another artist as a studio referral", () => {
    /** "Se o cliente retornar ao estúdio e for encaminhado a outro artista, o
     * novo atendimento será considerado indicação do estúdio." */
    expect(suggestion.for(client(), "a2")).toBe("STUDIO_REFERRAL");
  });

  it("treats a client the studio brought as a studio referral", () => {
    expect(suggestion.for(client({ broughtByArtistId: null }), "a1")).toBe("STUDIO_REFERRAL");
  });

  /** Errar para este lado paga a menos até alguém conferir; errar para o outro
   * paga a mais e exige cobrar de volta. Os cadastros anteriores à migração
   * `0008` estão todos aqui. */
  it("falls back to the studio when it cannot tell", () => {
    expect(suggestion.for(null, "a1")).toBe("STUDIO_REFERRAL");
    expect(suggestion.for(client(), null)).toBe("STUDIO_REFERRAL");
  });
});
