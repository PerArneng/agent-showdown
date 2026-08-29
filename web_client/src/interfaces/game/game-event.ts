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

export interface PlayerTurnStartedEvent {
  readonly type: "player_turn_started";
  readonly player: string;
}

export interface PlayerTurnEndedEvent {
  readonly type: "player_turn_ended";
  readonly player: string;
  readonly seconds: number;
}

/** Snake_case throughout: this is wire data, mirroring `interfaces/game/player_stats.py`. */
export interface PlayerStats {
  readonly turns: number;
  readonly total_seconds: number;
  readonly average_seconds: number;
  readonly eliminations: number;
  readonly deaths: number;
  readonly wins: number;
}

export interface PlayerDeadEvent {
  readonly type: "player_dead";
  readonly player: string;
}

/** A spell in flight. `path` is every square it travelled through, in order. */
export interface SpellCastEvent {
  readonly type: "spell_cast";
  readonly player: string;
  readonly spell: string;
  readonly direction: string;
  readonly origin: Position;
  readonly path: readonly Position[];
}

/** `player` was hit, `source` cast it. */
export interface PlayerHitEvent {
  readonly type: "player_hit";
  readonly player: string;
  readonly source: string;
  readonly spell: string;
  readonly damage: number;
  readonly position: Position;
}

export interface PlayerUpdatedEvent {
  readonly type: "player_updated";
  readonly player: string;
  readonly health: number;
}

export interface PlayerStatsEvent {
  readonly type: "player_stats";
  readonly player: string;
  readonly stats: PlayerStats;
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
  | PlayerTurnStartedEvent
  | PlayerTurnEndedEvent
  | PlayerStatsEvent
  | PlayerMovedEvent
  | PlayerReasonedEvent
  | PlayerDeadEvent
  | SpellCastEvent
  | PlayerHitEvent
  | PlayerUpdatedEvent
  | MoveBlockedEvent
  | TurnFailedEvent
  | GameEndedEvent;
