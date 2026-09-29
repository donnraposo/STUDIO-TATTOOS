import { describe, expect, it } from "vitest";

import { LanePacker } from "@/features/scheduling/LanePacker";

/** O que se protege aqui é a RN-AGE-004: solicitações concorrentes têm de
 * aparecer **juntas**. Se duas caíssem na mesma trilha, uma esconderia a
 * outra e o gestor decidiria sem saber que havia concorrência. */
interface Span {
  name: string;
  column: number;
  span: number;
}

const packer = new LanePacker();
const extent = (item: Span) => ({ column: item.column, span: item.span });

describe("LanePacker", () => {
  it("keeps bookings that do not overlap on a single track", () => {
    const packed = packer.pack(
      [
        { name: "morning", column: 1, span: 4 },
        { name: "afternoon", column: 9, span: 4 },
      ],
      extent,
    );

    expect(packed.map((entry) => entry.track)).toEqual([0, 0]);
    expect(packer.trackCount(packed)).toBe(1);
  });

  it("separates two competing requests so both stay visible", () => {
    const packed = packer.pack(
      [
        { name: "first", column: 1, span: 4 },
        { name: "second", column: 2, span: 4 },
      ],
      extent,
    );

    expect(packer.trackCount(packed)).toBe(2);
    expect(packed.map((entry) => entry.track).sort()).toEqual([0, 1]);
  });

  it("treats a booking that starts exactly when another ends as free", () => {
    /** RN-AGE-001: não há pausa obrigatória entre agendamentos da mesma maca,
     * então encostar não é sobrepor. */
    const packed = packer.pack(
      [
        { name: "first", column: 1, span: 4 },
        { name: "next", column: 5, span: 2 },
      ],
      extent,
    );

    expect(packer.trackCount(packed)).toBe(1);
  });

  it("reuses a track that has already been freed", () => {
    const packed = packer.pack(
      [
        { name: "a", column: 1, span: 4 },
        { name: "b", column: 2, span: 2 },
        { name: "c", column: 6, span: 2 },
      ],
      extent,
    );

    const byName = Object.fromEntries(packed.map((e) => [e.item.name, e.track]));
    expect(byName.a).toBe(0);
    expect(byName.b).toBe(1);
    expect(byName.c).toBe(0);
    expect(packer.trackCount(packed)).toBe(2);
  });

  it("orders by start, whatever order the API returned", () => {
    const packed = packer.pack(
      [
        { name: "late", column: 9, span: 2 },
        { name: "early", column: 1, span: 2 },
      ],
      extent,
    );

    expect(packed[0].item.name).toBe("early");
  });

  it("reports one track for an empty booth, so the lane keeps its height", () => {
    expect(packer.trackCount(packer.pack([], extent))).toBe(1);
  });
});
