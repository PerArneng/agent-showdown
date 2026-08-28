import type { Position } from "./position.js";

/** One contestant, as the client knows it: where it stands and what color it draws in. */
export interface PlayerState {
  readonly name: string;
  readonly position: Position;
  readonly color: string;
}
