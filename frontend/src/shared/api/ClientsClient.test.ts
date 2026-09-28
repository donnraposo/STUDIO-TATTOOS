import { afterEach, describe, expect, it, vi } from "vitest";

import { isFullRecord } from "@/shared/domain/Client";
import { ClientsClient } from "@/shared/api/ClientsClient";
import { HttpClient } from "@/shared/api/HttpClient";

/** O que importa aqui é a tradução: a API fala `snake_case` e devolve **duas**
 * formas diferentes para o mesmo cliente, conforme quem pergunta (RN-CLI-004).
 * Confundir as duas faria a tela mostrar campos vazios no lugar de dizer que
 * aquilo não é a ficha inteira. */

const FULL = {
  id: "c1",
  name: "Niamh",
  phone: "+353 87 111 1111",
  instagram: "@niamh",
  registered_by_artist_id: "a1",
  created_at: "2026-09-01T10:00:00+01:00",
};

const CONTACT = { id: "c2", name: "Declan", phone: "+353 86 222 2222", instagram: null };

function respondWith(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ClientsClient", () => {
  it("translates the listing into the shape the screens use", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith([FULL]));

    const [client] = await new ClientsClient(new HttpClient()).list();

    expect(client).toEqual({
      id: "c1",
      name: "Niamh",
      phone: "+353 87 111 1111",
      instagram: "@niamh",
      registeredByArtistId: "a1",
      createdAt: "2026-09-01T10:00:00+01:00",
    });
  });

  it("keeps the duplicate alert together with the created client", async () => {
    /** RN-CLI-005: alerta sem bloquear. O cliente vem criado **e** o aviso
     * junto; separar os dois faria a tela tratar o aviso como falha. */
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith({ client: FULL, possible_duplicates: [CONTACT] }),
    );

    const registered = await new ClientsClient(new HttpClient()).register(
      "Niamh",
      "+353 87 111 1111",
      null,
    );

    expect(registered.client.id).toBe("c1");
    expect(registered.possibleDuplicates).toEqual([
      { id: "c2", name: "Declan", phone: "+353 86 222 2222", instagram: null },
    ]);
  });

  it("recognises the reduced projection the studio sends about someone else's client", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith(CONTACT));

    const found = await new ClientsClient(new HttpClient()).find("c2");

    expect(isFullRecord(found)).toBe(false);
    expect(found).toEqual({
      id: "c2",
      name: "Declan",
      phone: "+353 86 222 2222",
      instagram: null,
    });
  });

  it("recognises the full record when the artist may see it", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith(FULL));

    const found = await new ClientsClient(new HttpClient()).find("c1");

    expect(isFullRecord(found)).toBe(true);
  });
});
