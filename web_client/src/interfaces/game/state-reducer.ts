import type { ClientState } from "./client-state.js";
import type { GameEvent } from "./game-event.js";

/** Folds events into state. Pure: no DOM, no canvas, no time. */
export interface StateReducer {
  initial(): ClientState;
  reduce(state: ClientState, event: GameEvent): ClientState;
}
