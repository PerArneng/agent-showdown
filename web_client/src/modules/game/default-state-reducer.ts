import type {
  ClientState,
  GameEvent,
  PlayerState,
  Position,
  StateReducer,
} from "../../interfaces/game/index.js";
import type { Palette } from "./palette.js";

/**
 * The whole client's logic: state and an event in, new state out.
 *
 * Pure and total. Every branch returns a fresh object, so nothing on screen can drift out of step
 * with what the server said.
 */
export class DefaultStateReducer implements StateReducer {
  constructor(private readonly palette: Palette) {}

  initial(): ClientState {
    return { board: null, players: [], status: "Waiting.", playing: false };
  }

  reduce(state: ClientState, event: GameEvent): ClientState {
    switch (event.type) {
      case "game_started":
        return { ...state, board: event.board, status: `Playing ${event.max_rounds} rounds.` };
      case "player_joined":
        return { ...state, players: this.joined(state, event.player, event.position) };
      case "round_started":
        return { ...state, status: `Round ${event.round_number}.`, playing: true };
      case "player_moved":
        // A client that connected mid-game never saw the join, so a move introduces the player.
        return { ...state, players: this.moved(state, event.player, event.destination) };
      case "player_reasoned":
        return { ...state, players: this.reasoned(state, event.player, event.reasoning) };
      case "move_blocked":
        return state;
      case "turn_failed":
        return { ...state, status: `${event.player} failed its turn: ${event.reason}` };
      case "game_ended":
        return {
          ...state,
          status: `Game over after ${event.rounds_played} rounds.`,
          playing: false,
        };
    }
  }

  private joined(state: ClientState, name: string, position: Position): readonly PlayerState[] {
    const known = state.players.find((player) => player.name === name);
    if (known !== undefined) {
      return this.moved(state, name, position);
    }
    const color = this.palette.colorFor(state.players.length);
    return [...state.players, { name, position, color, reasoning: "" }];
  }

  private moved(state: ClientState, name: string, position: Position): readonly PlayerState[] {
    if (!state.players.some((player) => player.name === name)) {
      return [
        ...state.players,
        { name, position, color: this.palette.colorFor(state.players.length), reasoning: "" },
      ];
    }
    return state.players.map((player) => (player.name === name ? { ...player, position } : player));
  }

  private reasoned(state: ClientState, name: string, reasoning: string): readonly PlayerState[] {
    // A client that connected mid-game may hear a player think before it sees it move.
    if (!state.players.some((player) => player.name === name)) {
      return [
        ...state.players,
        {
          name,
          position: { x: 0, y: 0 },
          color: this.palette.colorFor(state.players.length),
          reasoning,
        },
      ];
    }
    return state.players.map((player) =>
      player.name === name ? { ...player, reasoning } : player,
    );
  }
}
