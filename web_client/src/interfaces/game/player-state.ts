import type { Position } from "./position.js";

/** One contestant, as the client knows it: where it stands, what color and sprite it draws with, and why. */
export interface PlayerState {
  readonly name: string;
  readonly position: Position;
  readonly color: string;
  readonly sprite: number;
  /** The last thing this player said about its plan. Empty until it says something. */
  readonly reasoning: string;
  /** Wall seconds its last turn took. Zero until it has finished one. */
  readonly thinkSeconds: number;
  /** Cumulative wall seconds across all completed turns from protocol stats. */
  readonly totalThinkSeconds: number;
  /** Number of completed turns from protocol stats. */
  readonly turnsPlayed: number;
  /** Average wall seconds per turn from protocol stats. Zero until reported. */
  readonly averageThinkSeconds: number;
}
