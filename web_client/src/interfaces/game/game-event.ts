import type { Board } from "./board.js";
import type { Position } from "./position.js";

/**
 * Mirrors `interfaces/game/*_event.py`, discriminated on `type` exactly as the Pydantic union is.
 * Written by hand for now; generating it from the server's JSON schema is the obvious follow-up.
 */
export interface GameStartedEvent {
  readonly type: "game_started";
  readonly board: Board;
  readonly max_rounds: number;
}

export interface PlayerJoinedEvent {
  readonly type: "player_joined";
  readonly player: string;
  readonly position: Position;
}

export interface RoundStartedEvent {
  readonly type: "round_started";
  readonly round_number: number;
}

export interface PlayerMovedEvent {
  readonly type: "player_moved";
  readonly player: string;
  readonly source: Position;
  readonly destination: Position;
}

export interface PlayerReasonedEvent {
  readonly type: "player_reasoned";
  readonly player: string;
  readonly reasoning: string;
}

export interface MoveBlockedEvent {
  readonly type: "move_blocked";
  readonly player: string;
  readonly position: Position;
  readonly direction: string;
}

export interface TurnFailedEvent {
  readonly type: "turn_failed";
  readonly player: string;
  readonly reason: string;
}

export interface GameEndedEvent {
  readonly type: "game_ended";
  readonly rounds_played: number;
}

export type GameEvent =
  | GameStartedEvent
  | PlayerJoinedEvent
  | RoundStartedEvent
  | PlayerMovedEvent
  | PlayerReasonedEvent
  | MoveBlockedEvent
  | TurnFailedEvent
  | GameEndedEvent;
