import { afterEach, describe, expect, it, vi } from "vitest";

import { HttpClient } from "@/shared/api/HttpClient";
import { QuotesClient } from "@/shared/api/QuotesClient";

/** O que importa aqui é a tradução entre o `snake_case` da API e o `camelCase`
 * das telas, e sobretudo que **dinheiro e percentual continuem texto**. Passar
 * por `number` em qualquer ponto deste caminho reintroduziria o arredondamento
 * binário que o `Numeric(12, 2)` do banco existe para evitar. */

const QUOTE = {
  id: "q1",
  client_id: "c1",
  artist_id: "a1",
  origin: "ARTIST_OWN",
  description: "Full sleeve",
  body_region: "Right arm",
  size_estimate: "Full sleeve",
  total_value: "1200.00",
  planned_sessions: 4,
  planned_value_per_session: "300.00",
  estimated_duration_minutes: 180,
  notes: null,
  status: "PENDING",
  artist_percentage: null,
  approved_at: null,
  rejection_reason: null,
  rejection_note: null,
  created_at: "2026-09-20T10:00:00+01:00",
};

function respondWith(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("QuotesClient", () => {
  it("translates the listing into the shape the screens use", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith([QUOTE]));

    const [quote] = await new QuotesClient(new HttpClient()).list();

    expect(quote).toEqual({
      id: "q1",
      clientId: "c1",
      artistId: "a1",
      origin: "ARTIST_OWN",
      description: "Full sleeve",
      bodyRegion: "Right arm",
      sizeEstimate: "Full sleeve",
      totalValue: "1200.00",
      plannedSessions: 4,
      plannedValuePerSession: "300.00",
      estimatedDurationMinutes: 180,
      notes: null,
      status: "PENDING",
      artistPercentage: null,
      approvedAt: null,
      rejectionReason: null,
      rejectionNote: null,
      createdAt: "2026-09-20T10:00:00+01:00",
    });
  });

  it("sends the client and the artist only when creating", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith(QUOTE));
    const client = new QuotesClient(new HttpClient());

    await client.create(
      "c1",
      {
        origin: "STUDIO_REFERRAL",
        description: "Full sleeve",
        bodyRegion: "Right arm",
        sizeEstimate: "Full sleeve",
        totalValue: "1200.00",
        plannedSessions: 4,
        plannedValuePerSession: "300.00",
        estimatedDurationMinutes: 180,
        notes: null,
      },
      "a2",
    );

    const body = JSON.parse(String(fetchSpy.mock.calls[0]?.[1]?.body));
    expect(body.client_id).toBe("c1");
    expect(body.artist_id).toBe("a2");
    expect(body.total_value).toBe("1200.00");
  });

  /** RN-ORC-003: a edição trata dos campos do trabalho, não de para quem ele é.
   * Reatribuir o orçamento a outro cliente seria outro atendimento. */
  it("leaves the client and the artist out of an update", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith(QUOTE));

    await new QuotesClient(new HttpClient()).update("q1", {
      origin: "ARTIST_OWN",
      description: "Full sleeve",
      bodyRegion: "Right arm",
      sizeEstimate: "Full sleeve",
      totalValue: "1300.00",
      plannedSessions: 4,
      plannedValuePerSession: "325.00",
      estimatedDurationMinutes: 180,
      notes: "Client asked for more detail",
    });

    const [url, init] = fetchSpy.mock.calls[0] ?? [];
    const body = JSON.parse(String(init?.body));
    expect(String(url)).toBe("/api/v1/quotes/q1");
    expect(init?.method).toBe("PUT");
    expect(body).not.toHaveProperty("client_id");
    expect(body).not.toHaveProperty("artist_id");
  });

  /** RN-REP-006: o percentual congelado volta como texto, e a tela o mostra sem
   * recalcular nada. */
  it("keeps the frozen percentage as text", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith({
        ...QUOTE,
        status: "APPROVED",
        artist_percentage: "70.00",
        approved_at: "2026-09-21T11:00:00+01:00",
      }),
    );

    const approved = await new QuotesClient(new HttpClient()).approve("q1", null);

    expect(approved.artistPercentage).toBe("70.00");
    expect(approved.status).toBe("APPROVED");
  });

  it("sends the image as multipart without setting the content type by hand", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith({
        id: "i1",
        content_type: "image/png",
        byte_size: 2048,
        uploaded_at: "2026-09-21T11:00:00+01:00",
        content_path: "/api/v1/quotes/q1/reference-images/i1/content",
      }),
    );

    const image = await new QuotesClient(new HttpClient()).attachImage(
      "q1",
      new File(["x"], "reference.png", { type: "image/png" }),
    );

    const init = fetchSpy.mock.calls[0]?.[1];
    expect(init?.body).toBeInstanceOf(FormData);
    expect((init?.headers as Record<string, string>)["Content-Type"]).toBeUndefined();
    expect(image.contentPath).toBe("/api/v1/quotes/q1/reference-images/i1/content");
  });
});
