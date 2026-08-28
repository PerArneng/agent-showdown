import { describe, expect, it } from "vitest";
import demoGame from "../../fixtures/demo-game.json" with { type: "json" };
import type { GameEvent } from "../../src/interfaces/game/index.js";

/**
 * The fixture is a recording of the real server. If the event shapes on the Python side ever drift
 * from `game-event.ts`, this is where it shows up.
 */
describe("the demo fixture", () => {
  const events = demoGame as readonly GameEvent[];

  it("is a whole game", () => {
    expect(events.at(0)?.type).toBe("player_joined");
    expect(events.some((event) => event.type === "game_started")).toBe(true);
    expect(events.at(-1)).toEqual({ type: "game_ended", rounds_played: 10 });
  });

  it("records what the built-in agent was thinking", () => {
    const reasoned = events.filter((event) => event.type === "player_reasoned");
    expect(reasoned.some((event) => event.player === "simple-strands-1")).toBe(true);
  });

  it("only contains event types the client knows", () => {
    const known = new Set([
      "game_started",
      "player_joined",
      "round_started",
      "player_moved",
      "player_reasoned",
      "move_blocked",
      "turn_failed",
      "game_ended",
    ]);

    expect(events.filter((event) => !known.has(event.type))).toEqual([]);
  });
});
