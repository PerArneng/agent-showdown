import type { Board } from "./board.js";
import type { PlayerState } from "./player-state.js";
import type { VisualEffect } from "./visual-effect.js";

/** Everything on screen, as one value. Replaced on every event, never mutated. */
export interface ClientState {
  readonly board: Board | null;
  readonly players: readonly PlayerState[];
  readonly status: string;
  readonly playing: boolean;
  /** No robots are registered, so the arena is idle rather than between matches. */
  readonly paused: boolean;
  /** Who is in the arena. Robots appear here before any match has seated them. */
  readonly registered: readonly string[];
  /** The name of the player currently executing its turn, or null when idle. */
  readonly thinking: string | null;
  /** In-flight visual animation effect, or null/undefined when idle. */
  readonly effect?: VisualEffect | null;
}
