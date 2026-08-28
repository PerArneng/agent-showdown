import type { Board } from "./board.js";
import type { PlayerState } from "./player-state.js";

/** Everything on screen, as one value. Replaced on every event, never mutated. */
export interface ClientState {
  readonly board: Board | null;
  readonly players: readonly PlayerState[];
  readonly status: string;
  readonly playing: boolean;
}
