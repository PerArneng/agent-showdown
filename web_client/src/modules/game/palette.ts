/** Player colors, handed out by join order. Pure: the same seat always gets the same color. */
export class Palette {
  private static readonly COLORS = [
    "#4c8dff",
    "#ff5d7a",
    "#3ddc97",
    "#ffb454",
    "#c07cff",
    "#3ddbe0",
  ] as const;

  colorFor(seat: number): string {
    return Palette.COLORS[seat % Palette.COLORS.length] ?? Palette.COLORS[0];
  }
}
