import type {
  ClientState,
  GameEvent,
  GameSnapshot,
  PlayerState,
  PlayerStats,
  Position,
  SpritePicker,
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
  constructor(
    private readonly palette: Palette,
    private readonly spritePicker: SpritePicker,
  ) {}

  initial(): ClientState {
    return {
      board: null,
      players: [],
      status: "Waiting.",
      playing: false,
      paused: false,
      registered: [],
      thinking: null,
    };
  }

  catchUp(state: ClientState, snapshot: GameSnapshot): ClientState {
    // Gaps only. The stream is live and the snapshot was taken before it was asked for, so
    // anything the events already told us is the fresher truth and stays.
    const board = state.board ?? snapshot.board;
    const players = snapshot.players.reduce(
      (known: ClientState, player) =>
        known.players.some((seen) => seen.name === player.name)
          ? known
          : {
              ...known,
              players: this.introduce(
                known,
                player.name,
                player.position,
                player.reasoning,
                player.think_seconds,
                undefined,
                player.health,
              ),
            },
      state,
    ).players;
    const status =
      state.playing || !snapshot.playing ? state.status : `Round ${snapshot.round_number}.`;
    // Gaps only, like everything else here: anything the stream already told us stays.
    const registered =
      state.registered.length > 0 ? state.registered : [...snapshot.registered];
    return { ...state, board, players, status, registered, thinking: state.thinking };
  }

  reduce(state: ClientState, event: GameEvent): ClientState {
    switch (event.type) {
      case "arena_paused":
        return {
          ...state,
          paused: true,
          playing: false,
          thinking: null,
          status: "Waiting for a robot to join.",
        };
      case "arena_resumed":
        return { ...state, paused: false, status: "A robot joined." };
      case "player_registered":
        // In the arena, not yet on the board: it is seated when the next match starts.
        return state.registered.includes(event.player)
          ? state
          : { ...state, registered: [...state.registered, event.player] };
      case "player_unregistered":
        return {
          ...state,
          registered: state.registered.filter((name) => name !== event.player),
        };
      case "game_started":
        return {
          ...state,
          board: event.board,
          status: `Playing ${event.max_rounds} rounds.`,
          playing: true,
          thinking: null,
        };
      case "player_joined":
        return { ...state, players: this.joined(state, event.player, event.position) };
      case "round_started":
        return { ...state, status: `Round ${event.round_number}.`, playing: true };
      case "player_moved":
        // A client that connected mid-game never saw the join, so a move introduces the player.
        return { ...state, players: this.moved(state, event.player, event.destination) };
      case "player_turn_started":
        return {
          ...state,
          thinking: event.player,
          players: this.startedTurn(state, event.player),
        };
      case "player_turn_ended":
        return {
          ...state,
          thinking: state.thinking === event.player ? null : state.thinking,
          players: this.thought(state, event.player, event.seconds),
        };
      case "player_stats":
        return { ...state, players: this.stats(state, event.player, event.stats) };
      case "player_reasoned":
        return { ...state, players: this.reasoned(state, event.player, event.reasoning) };
      case "move_blocked":
        return state;
      case "spell_cast":
        return { ...state, status: `${event.player} cast ${event.spell}.` };
      case "player_hit":
        return {
          ...state,
          status: `${event.source} hit ${event.player} with ${event.spell} for ${event.damage} damage.`,
        };
      case "player_updated":
        return { ...state, players: this.updatedHealth(state, event.player, event.health) };
      case "player_dead":
        // Deadness is derived from health <= 0. player_dead fires when a turn is skipped.
        return state;
      case "turn_failed":
        return { ...state, status: `${event.player} failed its turn: ${event.reason}` };
      case "game_ended":
        return {
          ...state,
          status: `Game over after ${event.rounds_played} rounds.`,
          playing: false,
          thinking: null,
        };
    }
  }

  private startedTurn(state: ClientState, name: string): readonly PlayerState[] {
    if (!state.players.some((player) => player.name === name)) {
      return this.introduce(state, name, { x: 0, y: 0 }, "");
    }
    return state.players;
  }

  private joined(state: ClientState, name: string, position: Position): readonly PlayerState[] {
    const known = state.players.find((player) => player.name === name);
    if (known !== undefined) {
      return this.rejoined(state, name, position);
    }
    return this.introduce(state, name, position, "");
  }

  private rejoined(state: ClientState, name: string, position: Position): readonly PlayerState[] {
    return state.players.map((player) =>
      player.name === name
        ? {
            ...player,
            position,
            health: 100,
            thinkSeconds: 0,
            reasoning: "",
          }
        : player,
    );
  }

  private moved(state: ClientState, name: string, position: Position): readonly PlayerState[] {
    if (!state.players.some((player) => player.name === name)) {
      return this.introduce(state, name, position, "");
    }
    return state.players.map((player) => (player.name === name ? { ...player, position } : player));
  }

  private reasoned(state: ClientState, name: string, reasoning: string): readonly PlayerState[] {
    // A client that connected mid-game may hear a player think before it sees it move.
    if (!state.players.some((player) => player.name === name)) {
      return this.introduce(state, name, { x: 0, y: 0 }, reasoning);
    }
    return state.players.map((player) =>
      player.name === name ? { ...player, reasoning } : player,
    );
  }

  private thought(state: ClientState, name: string, seconds: number): readonly PlayerState[] {
    // A client that connected mid-game may see a turn end before it sees the player anywhere.
    if (!state.players.some((player) => player.name === name)) {
      return this.introduce(state, name, { x: 0, y: 0 }, "", seconds);
    }
    return state.players.map((player) =>
      player.name === name ? { ...player, thinkSeconds: seconds } : player,
    );
  }

  private updatedHealth(state: ClientState, name: string, health: number): readonly PlayerState[] {
    if (!state.players.some((player) => player.name === name)) {
      return this.introduce(state, name, { x: 0, y: 0 }, "", 0, undefined, health);
    }
    return state.players.map((player) => (player.name === name ? { ...player, health } : player));
  }

  private stats(state: ClientState, name: string, stats: PlayerStats): readonly PlayerState[] {
    // A client that connected mid-game may hear stats before it sees the player anywhere.
    if (!state.players.some((player) => player.name === name)) {
      return this.introduce(state, name, { x: 0, y: 0 }, "", 0, stats);
    }
    return state.players.map((player) =>
      player.name === name
        ? {
            ...player,
            turnsPlayed: stats.turns,
            totalThinkSeconds: stats.total_seconds,
            averageThinkSeconds: stats.average_seconds,
            eliminations: stats.eliminations,
            deaths: stats.deaths,
            wins: stats.wins,
          }
        : player,
    );
  }

  /** A player the client has not seen before, given the next color and a free sprite. */
  private introduce(
    state: ClientState,
    name: string,
    position: Position,
    reasoning: string,
    thinkSeconds = 0,
    stats?: PlayerStats,
    health = 100,
  ): readonly PlayerState[] {
    const color = this.palette.colorFor(state.players.length);
    const sprite = this.spritePicker.pick(
      name,
      state.players.map((player) => player.sprite),
    );
    const totalThinkSeconds = stats?.total_seconds ?? 0;
    const turnsPlayed = stats?.turns ?? 0;
    const averageThinkSeconds = stats?.average_seconds ?? 0;
    const eliminations = stats?.eliminations ?? 0;
    const deaths = stats?.deaths ?? 0;
    const wins = stats?.wins ?? 0;
    return [
      ...state.players,
      {
        name,
        position,
        health,
        color,
        sprite,
        reasoning,
        thinkSeconds,
        totalThinkSeconds,
        turnsPlayed,
        averageThinkSeconds,
        eliminations,
        deaths,
        wins,
      },
    ];
  }
}
