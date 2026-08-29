import type { Obstacle } from "./obstacle.js";

/** The playing field, in cells.
 *
 * Terrain is fixed for a match, so it rides on the board rather than arriving as events — which
 * is also how it reaches us, inside `game_started` and inside the snapshot. It is optional
 * because the demo fixture is a recording made before terrain existed.
 */
export interface Board {
  readonly width: number;
  readonly height: number;
  readonly obstacles?: readonly Obstacle[];
}
