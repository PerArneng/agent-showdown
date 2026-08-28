import { describe, expect, it } from "vitest";
import type { ClientState, GameSnapshot } from "../../src/interfaces/game/index.js";
import { DefaultStateReducer, HashSpritePicker, Palette } from "../../src/modules/game/index.js";

const reducer = new DefaultStateReducer(new Palette(), new HashSpritePicker());
const empty = reducer.initial();

function after(state: ClientState, ...events: Parameters<typeof reducer.reduce>[1][]): ClientState {
  return events.reduce((current, event) => reducer.reduce(current, event), state);
}

describe("DefaultStateReducer", () => {
  it("starts with nothing on the board", () => {
    expect(empty).toEqual({ board: null, players: [], status: "Waiting.", playing: false });
  });

  it("takes the board from game_started", () => {
    const state = after(empty, {
      type: "game_started",
      board: { width: 10, height: 10 },
      max_rounds: 10,
    });

    expect(state.board).toEqual({ width: 10, height: 10 });
    expect(state.status).toBe("Playing 10 rounds.");
  });

  it("gives each player its own color and sprite, by join order and name", () => {
    const state = after(
      empty,
      { type: "player_joined", player: "one", position: { x: 0, y: 0 } },
      { type: "player_joined", player: "two", position: { x: 9, y: 9 } },
    );

    expect(state.players.map((player) => player.name)).toEqual(["one", "two"]);
    expect(state.players[0]?.color).not.toBe(state.players[1]?.color);
    expect(state.players[0]?.sprite).toBeGreaterThanOrEqual(0);
    expect(state.players[0]?.sprite).toBeLessThan(10);
    expect(state.players[1]?.sprite).toBeGreaterThanOrEqual(0);
    expect(state.players[1]?.sprite).toBeLessThan(10);
    expect(state.players[0]?.sprite).not.toBe(state.players[1]?.sprite);
  });

  it("moves a player without touching the others", () => {
    const joined = after(
      empty,
      { type: "player_joined", player: "one", position: { x: 0, y: 0 } },
      { type: "player_joined", player: "two", position: { x: 9, y: 9 } },
    );

    const state = after(joined, {
      type: "player_moved",
      player: "one",
      source: { x: 0, y: 0 },
      destination: { x: 1, y: 0 },
    });

    expect(state.players[0]?.position).toEqual({ x: 1, y: 0 });
    expect(state.players[1]?.position).toEqual({ x: 9, y: 9 });
  });

  it("adopts a player it never saw join", () => {
    // A client that connects mid-game misses the joins entirely.
    const state = after(empty, {
      type: "player_moved",
      player: "late",
      source: { x: 0, y: 0 },
      destination: { x: 1, y: 1 },
    });

    expect(state.players).toHaveLength(1);
    expect(state.players[0]?.position).toEqual({ x: 1, y: 1 });
  });

  it("remembers the latest reasoning against the player that gave it", () => {
    const joined = after(
      empty,
      { type: "player_joined", player: "one", position: { x: 0, y: 0 } },
      { type: "player_joined", player: "two", position: { x: 9, y: 9 } },
    );

    const state = after(
      joined,
      { type: "player_reasoned", player: "one", reasoning: "first thought" },
      { type: "player_reasoned", player: "one", reasoning: "second thought" },
    );

    expect(state.players[0]?.reasoning).toBe("second thought");
    expect(state.players[1]?.reasoning).toBe("");
  });

  it("adopts a player that thinks before it is seen to move", () => {
    const state = after(empty, {
      type: "player_reasoned",
      player: "late",
      reasoning: "just arrived",
    });

    expect(state.players).toHaveLength(1);
    expect(state.players[0]?.reasoning).toBe("just arrived");
  });

  it("leaves everything alone when a move is blocked", () => {
    const joined = after(empty, {
      type: "player_joined",
      player: "one",
      position: { x: 0, y: 0 },
    });

    const state = after(joined, {
      type: "move_blocked",
      player: "one",
      position: { x: 0, y: 0 },
      direction: "LEFT",
    });

    expect(state).toBe(joined);
  });

  it("reports a failed turn in the status line", () => {
    const state = after(empty, {
      type: "turn_failed",
      player: "one",
      reason: "TimeoutError: too slow",
    });

    expect(state.status).toBe("one failed its turn: TimeoutError: too slow");
  });

  it("tracks whether a game is in flight", () => {
    const playing = after(empty, { type: "round_started", round_number: 1 });
    expect(playing.playing).toBe(true);

    const ended = after(playing, { type: "game_ended", rounds_played: 10 });
    expect(ended.playing).toBe(false);
    expect(ended.status).toBe("Game over after 10 rounds.");
  });

  it("never mutates the state it was given", () => {
    const before = after(empty, {
      type: "player_joined",
      player: "one",
      position: { x: 0, y: 0 },
    });
    const snapshot = structuredClone(before);

    after(before, {
      type: "player_moved",
      player: "one",
      source: { x: 0, y: 0 },
      destination: { x: 5, y: 5 },
    });

    expect(before).toEqual(snapshot);
  });

  describe("catchUp", () => {
    const midGame: GameSnapshot = {
      board: { width: 10, height: 10 },
      max_rounds: 10,
      round_number: 4,
      playing: true,
      players: [
        { name: "one", position: { x: 1, y: 2 }, reasoning: "heading for the middle" },
        { name: "two", position: { x: 9, y: 9 }, reasoning: "" },
      ],
    };

    it("gives a late client the board it never heard about", () => {
      const state = reducer.catchUp(empty, midGame);

      expect(state.board).toEqual({ width: 10, height: 10 });
      expect(state.status).toBe("Round 4.");
    });

    it("brings the players it missed, with their positions and last plan", () => {
      const state = reducer.catchUp(empty, midGame);

      expect(state.players.map((player) => player.name)).toEqual(["one", "two"]);
      expect(state.players[0]?.position).toEqual({ x: 1, y: 2 });
      expect(state.players[0]?.reasoning).toBe("heading for the middle");
      expect(state.players[0]?.color).not.toBe(state.players[1]?.color);
      expect(state.players[0]?.sprite).not.toBe(state.players[1]?.sprite);
    });

    it("never overwrites what the live stream already said", () => {
      // The snapshot was taken before it was asked for, so an event that arrived meanwhile wins.
      const live = after(empty, {
        type: "player_moved",
        player: "one",
        source: { x: 1, y: 2 },
        destination: { x: 5, y: 5 },
      });

      const state = reducer.catchUp(live, midGame);

      expect(state.players.find((player) => player.name === "one")?.position).toEqual({
        x: 5,
        y: 5,
      });
      expect(state.players.map((player) => player.name)).toEqual(["one", "two"]);
    });

    it("leaves a board the stream already delivered alone", () => {
      const live = after(empty, {
        type: "game_started",
        board: { width: 3, height: 3 },
        max_rounds: 2,
      });

      expect(reducer.catchUp(live, midGame).board).toEqual({ width: 3, height: 3 });
    });

    it("keeps the live status once a round has been heard", () => {
      const live = after(empty, { type: "round_started", round_number: 7 });

      expect(reducer.catchUp(live, midGame).status).toBe("Round 7.");
    });

    it("changes nothing when there is no game to catch up on", () => {
      const nothing: GameSnapshot = {
        board: null,
        max_rounds: 0,
        round_number: 0,
        playing: false,
        players: [],
      };

      expect(reducer.catchUp(empty, nothing)).toEqual(empty);
    });
  });
});
