/** Picks a sprite index (0..9) for a player name, avoiding collisions where possible. */
export interface SpritePicker {
  pick(name: string, taken: readonly number[]): number;
}
