import type { ClientState } from "./client-state.js";
import type { GameEvent } from "./game-event.js";
import type { GameSnapshot } from "./game-snapshot.js";

/** Folds events into state. Pure: no DOM, no canvas, no time. */
export interface StateReducer {
  initial(): ClientState;
  reduce(state: ClientState, event: GameEvent): ClientState;
  /**
   * Folds in what the client missed by connecting late. Fills gaps only: anything already learned
   * from the live stream is fresher than the snapshot and wins.
   */
  catchUp(state: ClientState, snapshot: GameSnapshot): ClientState;
}
