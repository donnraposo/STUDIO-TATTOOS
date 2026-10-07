import { afterEach, describe, expect, it, vi } from "vitest";

import { AccountsClient } from "@/shared/api/AccountsClient";
import { HttpClient } from "@/shared/api/HttpClient";

/** Quem aparece no seletor de artista da nova reserva.
 *
 * O erro que importa aqui não é visual: agendar para uma conta bloqueada
 * criaria um compromisso que a própria pessoa não conseguiria ver, porque o
 * bloqueio derruba o acesso na hora (RN 2.5). */
function account(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: "1",
    email: "someone@studio.ie",
    full_name: "Someone Full",
    artist_name: null,
    phone: "+353 1 000 0000",
    role: "RESIDENT",
    acts_as_artist: false,
    status: "ACTIVE",
    ...overrides,
  };
}

function respondWith(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AccountsClient", () => {
  it("prefers the artist name, which is how the studio refers to the person", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith([account({ artist_name: "Vera" })]),
    );

    const [artist] = await new AccountsClient(new HttpClient()).listArtists();

    expect(artist.displayName).toBe("Vera");
  });

  it("falls back to the full name when there is no artist name", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith([account({ role: "OWNER", acts_as_artist: true, artist_name: null })]),
    );

    const [artist] = await new AccountsClient(new HttpClient()).listArtists();

    expect(artist.displayName).toBe("Someone Full");
  });

  it("leaves out a blocked account", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith([account({ status: "BLOCKED", artist_name: "Vera" })]),
    );

    expect(await new AccountsClient(new HttpClient()).listArtists()).toEqual([]);
  });

  it("leaves out a manager who does not tattoo", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith([account({ role: "MANAGER", acts_as_artist: false })]),
    );

    expect(await new AccountsClient(new HttpClient()).listArtists()).toEqual([]);
  });

  it("includes an owner who also tattoos", async () => {
    /** Proprietário e gerente mantêm a alçada administrativa quando atuam como
     * tatuadores, e passam a ter agenda própria (RN 2). */
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith([account({ role: "OWNER", acts_as_artist: true, artist_name: "Nyx" })]),
    );

    const [artist] = await new AccountsClient(new HttpClient()).listArtists();

    expect(artist).toEqual({ id: "1", displayName: "Nyx", role: "OWNER", tattoos: true });
  });

  it("includes a guest, who tattoos and books benches", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith([account({ role: "GUEST", artist_name: "Lu" })]),
    );

    expect(await new AccountsClient(new HttpClient()).listArtists()).toHaveLength(1);
  });
});
