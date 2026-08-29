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
    expect(empty).toEqual({
      board: null,
      players: [],
      status: "Waiting.",
      playing: false,
      thinking: null,
    });
  });

  it("takes the board from game_started and clears thinking", () => {
    const state = after(empty, {
      type: "game_started",
      board: { width: 10, height: 10 },
      max_rounds: 10,
    });

    expect(state.board).toEqual({ width: 10, height: 10 });
    expect(state.status).toBe("Playing 10 rounds.");
    expect(state.thinking).toBeNull();
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

  it("sets thinking when a player turn starts", () => {
    const joined = after(empty, {
      type: "player_joined",
      player: "one",
      position: { x: 0, y: 0 },
    });

    const state = after(joined, { type: "player_turn_started", player: "one" });

    expect(state.thinking).toBe("one");
  });

  it("adopts a player whose turn starts before it is seen anywhere", () => {
    const state = after(empty, { type: "player_turn_started", player: "late" });

    expect(state.thinking).toBe("late");
    expect(state.players).toHaveLength(1);
    expect(state.players[0]?.name).toBe("late");
  });

  it("records the seconds a finished turn took against the player and clears thinking", () => {
    const joined = after(
      empty,
      { type: "player_joined", player: "one", position: { x: 0, y: 0 } },
      { type: "player_joined", player: "two", position: { x: 9, y: 9 } },
      { type: "player_turn_started", player: "one" },
    );

    expect(joined.thinking).toBe("one");

    const state = after(joined, { type: "player_turn_ended", player: "one", seconds: 12.5 });

    expect(state.thinking).toBeNull();
    expect(state.players[0]?.thinkSeconds).toBe(12.5);
    expect(state.players[1]?.thinkSeconds).toBe(0);
  });

  it("updates player running totals, average, and combat series stats from player_stats", () => {
    const joined = after(empty, {
      type: "player_joined",
      player: "one",
      position: { x: 0, y: 0 },
    });

    const state = after(joined, {
      type: "player_stats",
      player: "one",
      stats: {
        turns: 3,
        total_seconds: 12.5,
        average_seconds: 4.1666666,
        eliminations: 2,
        deaths: 1,
        wins: 1,
      },
    });

    expect(state.players[0]?.turnsPlayed).toBe(3);
    expect(state.players[0]?.totalThinkSeconds).toBe(12.5);
    expect(state.players[0]?.averageThinkSeconds).toBe(4.1666666);
    expect(state.players[0]?.eliminations).toBe(2);
    expect(state.players[0]?.deaths).toBe(1);
    expect(state.players[0]?.wins).toBe(1);
  });

  it("updates player health from player_updated", () => {
    const joined = after(empty, {
      type: "player_joined",
      player: "one",
      position: { x: 0, y: 0 },
    });

    expect(joined.players[0]?.health).toBe(100);

    const damaged = after(joined, {
      type: "player_updated",
      player: "one",
      health: 60,
    });
    expect(damaged.players[0]?.health).toBe(60);

    const eliminated = after(damaged, {
      type: "player_updated",
      player: "one",
      health: 0,
    });
    expect(eliminated.players[0]?.health).toBe(0);
  });

  it("adopts a player seen first in player_updated", () => {
    const state = after(empty, {
      type: "player_updated",
      player: "late",
      health: 45,
    });

    expect(state.players).toHaveLength(1);
    expect(state.players[0]?.name).toBe("late");
    expect(state.players[0]?.health).toBe(45);
  });

  it("reports spell casting in the status line", () => {
    const state = after(empty, {
      type: "spell_cast",
      player: "caster",
      spell: "fireball",
      direction: "RIGHT",
      origin: { x: 0, y: 0 },
      path: [
        { x: 1, y: 0 },
        { x: 2, y: 0 },
      ],
    });

    expect(state.status).toBe("caster cast fireball.");
  });

  it("reports player hit in the status line", () => {
    const state = after(empty, {
      type: "player_hit",
      player: "target",
      source: "caster",
      spell: "fireball",
      damage: 40,
      position: { x: 2, y: 0 },
    });

    expect(state.status).toBe("caster hit target with fireball for 40 damage.");
  });

  it("leaves state intact on player_dead skip notification", () => {
    const joined = after(
      empty,
      { type: "player_joined", player: "one", position: { x: 0, y: 0 } },
      { type: "player_updated", player: "one", health: 0 },
    );

    const skipped = after(joined, { type: "player_dead", player: "one" });
    expect(skipped.players[0]?.health).toBe(0);
    expect(skipped.players[0]?.position).toEqual({ x: 0, y: 0 });
  });

  it("resets player position and health on new match join while preserving cumulative series stats", () => {
    const match1 = after(
      empty,
      { type: "player_joined", player: "one", position: { x: 0, y: 0 } },
      {
        type: "player_stats",
        player: "one",
        stats: {
          turns: 5,
          total_seconds: 10.0,
          average_seconds: 2.0,
          eliminations: 3,
          deaths: 0,
          wins: 1,
        },
      },
      { type: "player_moved", player: "one", source: { x: 0, y: 0 }, destination: { x: 4, y: 4 } },
      { type: "player_updated", player: "one", health: 20 },
      { type: "game_ended", rounds_played: 10 },
    );

    expect(match1.players[0]?.position).toEqual({ x: 4, y: 4 });
    expect(match1.players[0]?.health).toBe(20);

    const match2 = after(
      match1,
      { type: "game_started", board: { width: 10, height: 10 }, max_rounds: 10 },
      { type: "player_joined", player: "one", position: { x: 0, y: 0 } },
    );

    expect(match2.players[0]?.position).toEqual({ x: 0, y: 0 });
    expect(match2.players[0]?.health).toBe(100);
    expect(match2.players[0]?.eliminations).toBe(3);
    expect(match2.players[0]?.wins).toBe(1);
    expect(match2.players[0]?.turnsPlayed).toBe(5);
  });

  it("adopts a player whose stats arrive before it is seen anywhere", () => {
    const state = after(empty, {
      type: "player_stats",
      player: "late",
      stats: {
        turns: 2,
        total_seconds: 6.0,
        average_seconds: 3.0,
        eliminations: 0,
        deaths: 0,
        wins: 0,
      },
    });

    expect(state.players).toHaveLength(1);
    expect(state.players[0]?.name).toBe("late");
    expect(state.players[0]?.turnsPlayed).toBe(2);
    expect(state.players[0]?.totalThinkSeconds).toBe(6.0);
    expect(state.players[0]?.averageThinkSeconds).toBe(3.0);
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

  it("tracks whether a game is in flight and clears thinking when ended", () => {
    const playing = after(
      empty,
      { type: "round_started", round_number: 1 },
      { type: "player_turn_started", player: "one" },
    );
    expect(playing.playing).toBe(true);
    expect(playing.thinking).toBe("one");

    const ended = after(playing, { type: "game_ended", rounds_played: 10 });
    expect(ended.playing).toBe(false);
    expect(ended.thinking).toBeNull();
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
        {
          name: "one",
          position: { x: 1, y: 2 },
          health: 100,
          reasoning: "heading for the middle",
          think_seconds: 1.5,
        },
        { name: "two", position: { x: 9, y: 9 }, health: 100, reasoning: "", think_seconds: 0 },
      ],
    };

    it("carries the think time a late client never heard", () => {
      const state = reducer.catchUp(empty, midGame);

      expect(state.players[0]?.thinkSeconds).toBe(1.5);
    });

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
