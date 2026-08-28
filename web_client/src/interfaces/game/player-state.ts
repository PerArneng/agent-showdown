import type { Position } from "./position.js";

/** One contestant, as the client knows it: where it stands, what color and sprite it draws with, and why. */
export interface PlayerState {
  readonly name: string;
  readonly position: Position;
  readonly color: string;
  readonly sprite: number;
  /** The last thing this player said about its plan. Empty until it says something. */
  readonly reasoning: string;
}
