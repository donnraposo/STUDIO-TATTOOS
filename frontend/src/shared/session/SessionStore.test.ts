import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/shared/api/ApiError";
import type { AuthClient } from "@/shared/api/AuthClient";
import type { AuthenticatedUser } from "@/shared/api/AuthenticatedUser";
import { SessionStore } from "@/shared/session/SessionStore";

const OWNER: AuthenticatedUser = {
  id: "1",
  email: "owner@studio.ie",
  fullName: "Studio Owner",
  role: "OWNER",
  actsAsArtist: false,
};

function storeWith(auth: Partial<AuthClient>): SessionStore {
  return new SessionStore(auth as AuthClient);
}

describe("SessionStore", () => {
  it("recognises the session that the cookie still carries", async () => {
    const store = storeWith({ currentUser: vi.fn().mockResolvedValue(OWNER) });

    await store.restore();

    expect(store.user.value).toEqual(OWNER);
    expect(store.isRestoring.value).toBe(false);
  });

  it("treats an expired session as simply not signed in", async () => {
    const store = storeWith({
      currentUser: vi.fn().mockRejectedValue(new ApiError(401, "Authentication required.")),
    });

    await store.restore();

    expect(store.user.value).toBeNull();
  });

  it("does not stop the application from starting when the API is unreachable", async () => {
    /** Uma falha de rede aqui não pode virar tela branca: propagar impediria a
     * aplicação de montar, e o formulário de login mostra o erro real na
     * primeira tentativa. */
    const store = storeWith({
      currentUser: vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    });

    await expect(store.restore()).resolves.toBeUndefined();
    expect(store.user.value).toBeNull();
  });

  it("keeps who signed in", async () => {
    const store = storeWith({ login: vi.fn().mockResolvedValue(OWNER) });

    await store.signIn("owner@studio.ie", "correct horse battery staple");

    expect(store.user.value).toEqual(OWNER);
  });

  it("only forgets the user after the server ends the session", async () => {
    /** A ordem importa: esquecer antes e falhar a chamada deixaria a interface
     * achando que saiu enquanto a sessão seguiria válida no servidor. */
    const logout = vi.fn().mockRejectedValue(new ApiError(500, "Boom"));
    const store = storeWith({ login: vi.fn().mockResolvedValue(OWNER), logout });
    await store.signIn("owner@studio.ie", "correct horse battery staple");

    await expect(store.signOut()).rejects.toBeInstanceOf(ApiError);

    expect(store.user.value).toEqual(OWNER);
  });

  it("forgets the user when a request reports the session is gone", async () => {
    const store = storeWith({ login: vi.fn().mockResolvedValue(OWNER) });
    await store.signIn("owner@studio.ie", "correct horse battery staple");

    store.forget();

    expect(store.user.value).toBeNull();
  });
});
