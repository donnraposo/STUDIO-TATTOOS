import { describe, expect, it } from "vitest";

import { BookingPlacement } from "@/features/scheduling/BookingPlacement";

/** A grade cobre o expediente do estúdio: 10h às 20h, em faixas de 30 minutos
 * (`01_REGRAS_DE_NEGOCIO.md` §1.1). */
const placement = new BookingPlacement(10, 20, 30);

describe("BookingPlacement", () => {
  it("describes the grid the studio day needs", () => {
    expect(placement.slotCount).toBe(20);
    expect(placement.hourLabels).toEqual([
      "10:00",
      "11:00",
      "12:00",
      "13:00",
      "14:00",
      "15:00",
      "16:00",
      "17:00",
      "18:00",
      "19:00",
    ]);
  });

  it("places a booking that starts when the studio opens", () => {
    const placed = placement.place("2026-10-06T10:00:00+01:00", "2026-10-06T12:00:00+01:00");

    expect(placed).toEqual({ column: 1, span: 4, clipped: false });
  });

  it("places an afternoon booking on the right slot", () => {
    const placed = placement.place("2026-10-06T14:30:00+01:00", "2026-10-06T16:00:00+01:00");

    expect(placed).toEqual({ column: 10, span: 3, clipped: false });
  });

  it("reads the studio clock, not the browser clock", () => {
    /** O mesmo instante escrito com deslocamentos diferentes precisa cair na
     * mesma coluna. Se caísse em colunas diferentes, a agenda apareceria
     * deslocada para quem estivesse em outro fuso — e pareceria correta. */
    const withOffset = placement.place(
      "2026-10-06T14:30:00+01:00",
      "2026-10-06T16:00:00+01:00",
    );
    const inUtc = placement.place("2026-10-06T13:30:00+00:00", "2026-10-06T15:00:00+00:00");

    expect(withOffset).toEqual(inUtc);
  });

  it("trims a booking that started before the studio opened", () => {
    /** A sessão existe e ocupa a maca. Sumir da tela porque começou cedo
     * esconderia ocupação real. */
    const placed = placement.place("2026-10-06T09:00:00+01:00", "2026-10-06T11:00:00+01:00");

    expect(placed).toEqual({ column: 1, span: 2, clipped: true });
  });

  it("trims a booking that runs past closing time", () => {
    const placed = placement.place("2026-10-06T19:00:00+01:00", "2026-10-06T21:30:00+01:00");

    expect(placed).toEqual({ column: 19, span: 2, clipped: true });
  });

  it("leaves out a booking that never touches the working day", () => {
    expect(placement.place("2026-10-06T07:00:00+01:00", "2026-10-06T08:00:00+01:00")).toBeNull();
    expect(placement.place("2026-10-06T21:00:00+01:00", "2026-10-06T22:00:00+01:00")).toBeNull();
  });

  it("treats midnight as the end of the day, not the start", () => {
    /** Sem isto o bloco apareceria invertido, com fim antes do começo. */
    const placed = placement.place("2026-10-06T19:00:00+01:00", "2026-10-07T00:00:00+01:00");

    expect(placed).toEqual({ column: 19, span: 2, clipped: true });
  });

  it("never collapses a very short booking to nothing", () => {
    /** Meia faixa arredonda para uma: um bloco de largura zero seria invisível
     * e a maca pareceria livre. */
    const placed = placement.place("2026-10-06T10:00:00+01:00", "2026-10-06T10:10:00+01:00");

    expect(placed?.span).toBe(1);
  });
});
