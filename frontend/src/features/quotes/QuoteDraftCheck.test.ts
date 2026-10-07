import { describe, expect, it } from "vitest";

import { QuoteDraftCheck, type QuoteDraftInput } from "@/features/quotes/QuoteDraftCheck";

function draft(overrides: Partial<QuoteDraftInput> = {}): QuoteDraftInput {
  return {
    clientId: "client-1",
    description: "Full sleeve, black and grey",
    bodyRegion: "Right arm",
    sizeEstimate: "Full sleeve",
    totalValue: "1200.00",
    plannedSessions: "4",
    plannedValuePerSession: "300.00",
    estimatedDurationMinutes: "180",
    notes: "",
    ...overrides,
  };
}

describe("QuoteDraftCheck", () => {
  const check = new QuoteDraftCheck();

  it("accepts a complete draft", () => {
    const report = check.review(draft(), true);

    expect(report.errors).toEqual({});
    expect(report.submittable).toBe(true);
  });

  it("requires the client only when creating", () => {
    expect(check.review(draft({ clientId: "" }), true).errors.clientId).toBeDefined();
    expect(check.review(draft({ clientId: "" }), false).errors.clientId).toBeUndefined();
  });

  it("refuses blank text and text past the field limit", () => {
    expect(check.review(draft({ description: "   " }), true).errors.description).toBeDefined();
    expect(check.review(draft({ bodyRegion: "x".repeat(81) }), true).errors.bodyRegion).toBeDefined();
    expect(check.review(draft({ bodyRegion: "x".repeat(80) }), true).errors.bodyRegion).toBeUndefined();
  });

  it("refuses amounts that are not money in euro", () => {
    for (const value of ["", "abc", "-10", "10.005", "1e3", "10,50"]) {
      expect(check.review(draft({ totalValue: value }), true).errors.totalValue).toBeDefined();
    }
  });

  it("refuses zero and accepts one cent", () => {
    expect(check.review(draft({ totalValue: "0.00" }), true).errors.totalValue).toBeDefined();
    expect(check.review(draft({ totalValue: "0.01" }), true).errors.totalValue).toBeUndefined();
  });

  it("refuses fractional or absent counts", () => {
    expect(check.review(draft({ plannedSessions: "1.5" }), true).errors.plannedSessions).toBeDefined();
    expect(check.review(draft({ plannedSessions: "0" }), true).errors.plannedSessions).toBeDefined();
    expect(
      check.review(draft({ estimatedDurationMinutes: "" }), true).errors.estimatedDurationMinutes,
    ).toBeDefined();
  });

  it("adds up the sessions without binary rounding", () => {
    const report = check.review(
      draft({ plannedSessions: "3", plannedValuePerSession: "133.33", totalValue: "399.99" }),
      true,
    );

    expect(report.plannedTotal).toBe("399.99");
    expect(report.differsFromTotal).toBe(false);
    expect(report.exceedsTotal).toBe(false);
  });

  it("reports the sessions going over the total (RN-PAG-001) without blocking the draft", () => {
    const report = check.review(
      draft({ plannedSessions: "5", plannedValuePerSession: "300.00", totalValue: "1200.00" }),
      true,
    );

    expect(report.plannedTotal).toBe("1500.00");
    expect(report.exceedsTotal).toBe(true);
    expect(report.submittable).toBe(true);
  });

  it("reports the sessions falling short of the total", () => {
    const report = check.review(
      draft({ plannedSessions: "2", plannedValuePerSession: "300.00", totalValue: "1200.00" }),
      true,
    );

    expect(report.exceedsTotal).toBe(false);
    expect(report.differsFromTotal).toBe(true);
  });

  it("has no planned total while the numbers are unusable", () => {
    expect(check.review(draft({ plannedValuePerSession: "" }), true).plannedTotal).toBeNull();
    expect(check.review(draft({ plannedSessions: "" }), true).plannedTotal).toBeNull();
  });

  it("keeps cents that carry over into whole euro", () => {
    const report = check.review(
      draft({ plannedSessions: "4", plannedValuePerSession: "0.25", totalValue: "1.00" }),
      true,
    );

    expect(report.plannedTotal).toBe("1.00");
    expect(report.differsFromTotal).toBe(false);
  });
});
