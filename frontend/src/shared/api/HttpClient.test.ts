import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/shared/api/ApiError";
import { CookieReader } from "@/shared/api/CookieReader";
import { HttpClient } from "@/shared/api/HttpClient";

/** O cliente HTTP é a única costura com a rede, então o que se verifica aqui
 * vale para todas as telas de uma vez: o token CSRF só acompanha o que altera
 * estado, o 401 avisa quem precisa reagir, e resposta de erro que não é JSON
 * não derruba a explicação real. */

function respondWith(status: number, body: string, type = "application/json"): Response {
  return new Response(body, { status, headers: { "Content-Type": type } });
}

function clientWithCsrf(token: string | null): HttpClient {
  const cookie = token ? `studio_csrf=${token}` : "";
  return new HttpClient("/api/v1", new CookieReader(() => cookie));
}

function lastRequestHeaders(): Record<string, string> {
  const call = vi.mocked(globalThis.fetch).mock.calls.at(-1);
  return (call?.[1]?.headers ?? {}) as Record<string, string>;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("HttpClient", () => {
  it("does not send the CSRF token on a read", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith(200, '{"ok":true}'));

    await clientWithCsrf("token-123").get("/clients");

    expect(lastRequestHeaders()["X-CSRF-Token"]).toBeUndefined();
  });

  it("sends the CSRF token on a write", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith(200, '{"ok":true}'));

    await clientWithCsrf("token-123").post("/clients", { name: "Aoife" });

    expect(lastRequestHeaders()["X-CSRF-Token"]).toBe("token-123");
  });

  it("sends the session cookie on every call", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respondWith(200, "{}"));

    await clientWithCsrf("token-123").get("/auth/me");

    const call = vi.mocked(globalThis.fetch).mock.calls.at(-1);
    expect(call?.[1]?.credentials).toBe("include");
  });

  it("warns the application once the session is gone", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith(401, '{"detail":"Authentication required."}'),
    );
    const client = clientWithCsrf("token-123");
    const warned = vi.fn();
    client.whenUnauthenticated(warned);

    await expect(client.get("/clients")).rejects.toBeInstanceOf(ApiError);

    expect(warned).toHaveBeenCalledOnce();
  });

  it("marks a scheduling conflict so the screen can open the modal", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith(409, '{"detail":"This bench is already booked."}'),
    );

    await expect(clientWithCsrf(null).post("/bookings", {})).rejects.toMatchObject({
      status: 409,
      message: "This bench is already booked.",
    });
  });

  it("reads the field message out of a validation error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith(422, '{"detail":[{"msg":"Value must be greater than 0"}]}'),
    );

    await expect(clientWithCsrf(null).post("/quotes", {})).rejects.toMatchObject({
      message: "Value must be greater than 0",
    });
  });

  it("survives an error body that is not JSON", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respondWith(502, "<html>Bad gateway</html>", "text/html"),
    );

    await expect(clientWithCsrf(null).get("/clients")).rejects.toMatchObject({
      status: 502,
      message: "Request failed with status 502.",
    });
  });

  it("accepts an empty body on delete", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));

    await expect(clientWithCsrf("token-123").delete("/quotes/1/reference-images/2"))
      .resolves.toBeUndefined();
  });
});
