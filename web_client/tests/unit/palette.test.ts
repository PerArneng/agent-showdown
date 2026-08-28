import { describe, expect, it } from "vitest";
import { Palette } from "../../src/modules/game/index.js";

describe("Palette", () => {
  it("gives the same seat the same color every time", () => {
    const palette = new Palette();

    expect(palette.colorFor(0)).toBe(palette.colorFor(0));
  });

  it("gives neighbouring seats different colors", () => {
    const palette = new Palette();

    expect(palette.colorFor(0)).not.toBe(palette.colorFor(1));
  });

  it("wraps rather than running out", () => {
    const palette = new Palette();

    expect(palette.colorFor(600)).toBe(palette.colorFor(0));
  });
});
