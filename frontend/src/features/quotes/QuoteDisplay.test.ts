import { describe, expect, it } from "vitest";

import { QuoteDisplay } from "@/features/quotes/QuoteDisplay";

describe("QuoteDisplay", () => {
  const display = new QuoteDisplay();

  it("names every quote state in plain English", () => {
    expect(display.status("PENDING")).toEqual({ label: "Pending", tone: "warning" });
    expect(display.status("APPROVED")).toEqual({ label: "Approved", tone: "positive" });
    expect(display.status("REJECTED")).toEqual({ label: "Rejected", tone: "danger" });
  });

  it("names both origins", () => {
    expect(display.origin("ARTIST_OWN")).toBe("Artist's own client");
    expect(display.origin("STUDIO_REFERRAL")).toBe("Studio referral");
  });

  /** RN-REP-001 e RN-REP-002. É o número que a tela mostra antes da aprovação;
   * o que vale depois é o congelado pelo backend (RN-REP-006). */
  it("shows the studio standard share for each origin", () => {
    expect(display.standardPercentage("ARTIST_OWN")).toBe("70");
    expect(display.standardPercentage("STUDIO_REFERRAL")).toBe("50");
  });

  it("offers both origins to the form", () => {
    expect(display.origins()).toEqual(["ARTIST_OWN", "STUDIO_REFERRAL"]);
  });
});
