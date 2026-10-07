import { describe, expect, it } from "vitest";

import { ByteSize } from "@/shared/format/ByteSize";

describe("ByteSize", () => {
  const size = new ByteSize();

  it("keeps plain bytes whole", () => {
    expect(size.human(0)).toBe("0 B");
    expect(size.human(900)).toBe("900 B");
  });

  it("climbs the scale in multiples of 1024", () => {
    expect(size.human(1024)).toBe("1 KB");
    expect(size.human(1536)).toBe("1.5 KB");
    expect(size.human(1024 * 1024)).toBe("1 MB");
    expect(size.human(1024 * 1024 * 1024)).toBe("1 GB");
  });

  it("stops at the largest unit it knows", () => {
    expect(size.human(1024 ** 4)).toBe("1024 GB");
  });

  it("shows a dash instead of NaN", () => {
    expect(size.human(Number.NaN)).toBe("—");
    expect(size.human(-1)).toBe("—");
  });
});
