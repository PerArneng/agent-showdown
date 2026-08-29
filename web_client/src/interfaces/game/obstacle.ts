import type { Position } from "./position.js";

/** What stands on an obstructed square. Mirrors `TerrainKind` on the Python side. */
export type TerrainKind = "tree" | "stone_wall" | "boulder" | "stone_well";

/** One blocked square: nothing walks onto it and no bolt flies through it. */
export interface Obstacle {
  readonly position: Position;
  readonly kind: TerrainKind;
}
