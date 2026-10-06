import { describe, expect, it } from "vitest";

import { ArtistRole } from "@/shared/domain/ArtistRole";

/** RN 2.3. A resposta decide duas coisas que não são cosméticas: quem aparece
 * na agenda e no repasse, e quem precisa de nome de artista — o banco recusa
 * artista sem ele, em `ck_user_account_artist_name_required`.
 */

describe("ArtistRole", () => {
  const artists = new ArtistRole();

  it("treats resident and guest as artists by definition", () => {
    expect(artists.isAlways("RESIDENT")).toBe(true);
    expect(artists.isAlways("GUEST")).toBe(true);
  });

  /** O perfil de gestão não tatua por si. Se tatuasse, a caixa "also tattoos"
   * não precisaria existir — e sem ela o proprietário que atende ficaria fora
   * da agenda e do repasse. */
  it("does not assume management tattoos", () => {
    expect(artists.isAlways("OWNER")).toBe(false);
    expect(artists.isAlways("MANAGER")).toBe(false);
  });

  it("counts the management account that also tattoos", () => {
    expect(artists.includes("OWNER", true)).toBe(true);
    expect(artists.includes("MANAGER", true)).toBe(true);
    expect(artists.includes("MANAGER", false)).toBe(false);
  });

  /** A marca desligada não retira o artista do atendimento: residente tatua
   * pelo perfil, e lê-la como "não tatua" o tiraria da agenda. */
  it("keeps an artist an artist regardless of the flag", () => {
    expect(artists.includes("RESIDENT", false)).toBe(true);
    expect(artists.includes("GUEST", false)).toBe(true);
  });
});
