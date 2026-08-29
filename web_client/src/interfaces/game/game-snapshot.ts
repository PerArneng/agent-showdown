import type { Board } from "./board.js";
import type { Position } from "./position.js";

/** One contestant as the server remembers it. Mirrors `interfaces/game/player_snapshot.py`. */
export interface PlayerSnapshot {
  readonly name: string;
  readonly position: Position;
  readonly health: number;
  readonly reasoning: string;
  readonly think_seconds: number;
}

/**
 * The current game, fetched rather than streamed. Mirrors `interfaces/game/game_snapshot.py`.
 *
 * The event stream has no replay, so a client that connects mid-game never hears `game_started`
 * and has no board to draw. This is that missing state.
 */
export interface GameSnapshot {
  readonly board: Board | null;
  readonly max_rounds: number;
  readonly round_number: number;
  readonly playing: boolean;
  readonly players: readonly PlayerSnapshot[];
}
