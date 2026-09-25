import type { SystemStatus } from "@/shared/api/SystemStatus";

export class SystemStatusClient {
  private readonly endpoint: string;

  constructor(endpoint = "/api/v1/ready") {
    this.endpoint = endpoint;
  }

  async fetch(): Promise<SystemStatus> {
    try {
      const response = await globalThis.fetch(this.endpoint);
      const body = (await response.json()) as { database?: string };
      return {
        api: "reachable",
        database: body.database === "reachable" ? "reachable" : "unreachable",
      };
    } catch {
      return { api: "unreachable", database: "unreachable" };
    }
  }
}
