import { afterEach, describe, expect, it, vi } from "vitest";

import { SystemStatusClient } from "@/shared/api/SystemStatusClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SystemStatusClient", () => {
  it("reports both reachable when the API confirms the database", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ json: async () => ({ database: "reachable" }) }),
    );

    await expect(new SystemStatusClient().fetch()).resolves.toEqual({
      api: "reachable",
      database: "reachable",
    });
  });

  it("reports the database unreachable while the API still answers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ json: async () => ({ database: "unreachable" }) }),
    );

    await expect(new SystemStatusClient().fetch()).resolves.toEqual({
      api: "reachable",
      database: "unreachable",
    });
  });

  it("reports everything unreachable when the request itself fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    await expect(new SystemStatusClient().fetch()).resolves.toEqual({
      api: "unreachable",
      database: "unreachable",
    });
  });
});
