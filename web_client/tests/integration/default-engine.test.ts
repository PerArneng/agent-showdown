import { beforeEach, describe, expect, it } from "vitest";
import demoGame from "../../fixtures/demo-game.json" with { type: "json" };
import type { GameEvent, GameSnapshot } from "../../src/interfaces/game/index.js";
import { DefaultEngine } from "../../src/modules/engine/index.js";
import {
  BoardRenderer,
  DefaultStateReducer,
  HashSpritePicker,
  Palette,
} from "../../src/modules/game/index.js";
import {
  InMemoryConnectionIndicator,
  InMemoryPlayerList,
  InMemoryStartButton,
  InMemoryStatusText,
  RecordingCanvas,
  RecordingGameApi,
  ScriptedEventStream,
} from "../fakes/index.js";

/** The whole client, wired as `container.ts` wires it, with fakes at every edge. No DOM. */
class Fixture {
  readonly canvas = new RecordingCanvas(100, 100);
  readonly api: RecordingGameApi;
  readonly playerList = new InMemoryPlayerList();
  readonly statusText = new InMemoryStatusText();
  readonly startButton = new InMemoryStartButton();
  readonly connectionIndicator = new InMemoryConnectionIndicator();
  readonly engine: DefaultEngine;

  constructor(
    readonly stream: ScriptedEventStream,
    snapshot?: GameSnapshot,
  ) {
    this.api = new RecordingGameApi(snapshot);
    this.engine = new DefaultEngine(
      stream,
      this.api,
      new DefaultStateReducer(new Palette(), new HashSpritePicker()),
      new BoardRenderer(this.canvas),
      this.playerList,
      this.statusText,
      this.startButton,
      this.connectionIndicator,
    );
  }
}

describe("DefaultEngine", () => {
  let recorded: readonly GameEvent[];

  beforeEach(() => {
    recorded = demoGame as readonly GameEvent[];
  });

  it("plays a whole recorded game through to the sidebar", () => {
    const fixture = new Fixture(new ScriptedEventStream(recorded));

    fixture.engine.connect();

    expect(fixture.playerList.names()).toEqual(["dummy-1", "simple-strands-1"]);
    expect(fixture.statusText.last()).toBe("Game over after 10 rounds.");
  });

  it("leaves every player somewhere on the board it was told about", () => {
    const fixture = new Fixture(new ScriptedEventStream(recorded));

    fixture.engine.connect();

    for (const player of fixture.playerList.shown) {
      expect(player.position.x).toBeGreaterThanOrEqual(0);
      expect(player.position.x).toBeLessThan(10);
      expect(player.position.y).toBeGreaterThanOrEqual(0);
      expect(player.position.y).toBeLessThan(10);
    }
  });

  it("draws once per event", () => {
    const fixture = new Fixture(new ScriptedEventStream(recorded));

    fixture.engine.connect();

    // One clear on connect for the empty state, then one per event.
    expect(fixture.canvas.calls.filter((call) => call.kind === "clear")).toHaveLength(
      recorded.length + 1,
    );
  });

  it("disables the button on start and re-enables it when the game ends", () => {
    const stream = new ScriptedEventStream();
    const fixture = new Fixture(stream);
    fixture.engine.connect();

    fixture.startButton.click();
    expect(fixture.startButton.enabled).toBe(false);
    expect(fixture.api.started).toBe(1);

    stream.push({ type: "game_ended", rounds_played: 10 });
    expect(fixture.startButton.enabled).toBe(true);
  });

  it("clears the last game's players when a new one starts", () => {
    const fixture = new Fixture(new ScriptedEventStream(recorded));
    fixture.engine.connect();
    expect(fixture.playerList.names()).toHaveLength(2);

    fixture.startButton.click();

    expect(fixture.playerList.names()).toEqual([]);
    expect(fixture.statusText.last()).toBe("Starting.");
  });

  it("shows the empty state before anything has happened", () => {
    const fixture = new Fixture(new ScriptedEventStream());

    fixture.engine.connect();

    expect(fixture.playerList.names()).toEqual([]);
    expect(fixture.statusText.last()).toBe("Waiting.");
  });

  it("updates connection status indicator when stream connects and disconnects", () => {
    const stream = new ScriptedEventStream();
    const fixture = new Fixture(stream);

    fixture.engine.connect();
    expect(fixture.connectionIndicator.last()).toBe(true);

    stream.setConnected(false);
    expect(fixture.connectionIndicator.last()).toBe(false);

    stream.setConnected(true);
    expect(fixture.connectionIndicator.last()).toBe(true);
  });

  it("forwards active thinking state to player list when turns start and end", () => {
    const stream = new ScriptedEventStream();
    const fixture = new Fixture(stream);
    fixture.engine.connect();

    stream.push({ type: "player_joined", player: "alice", position: { x: 0, y: 0 } });
    stream.push({ type: "player_turn_started", player: "alice" });
    expect(fixture.playerList.thinking).toBe("alice");

    stream.push({ type: "player_turn_ended", player: "alice", seconds: 1.25 });
    expect(fixture.playerList.thinking).toBeNull();
    expect(fixture.playerList.shown[0]?.thinkSeconds).toBe(1.25);

    stream.push({
      type: "player_stats",
      player: "alice",
      stats: { turns: 1, total_seconds: 1.25, average_seconds: 1.25 },
    });
    expect(fixture.playerList.shown[0]?.totalThinkSeconds).toBe(1.25);
    expect(fixture.playerList.shown[0]?.turnsPlayed).toBe(1);
    expect(fixture.playerList.shown[0]?.averageThinkSeconds).toBe(1.25);
  });

  describe("connecting to a game already in progress", () => {
    const midGame: GameSnapshot = {
      board: { width: 10, height: 10 },
      max_rounds: 10,
      round_number: 4,
      playing: true,
      players: [
        {
          name: "one",
          position: { x: 1, y: 2 },
          reasoning: "heading for the middle",
          think_seconds: 1.5,
        },
      ],
    };

    it("draws the board it never heard game_started for", async () => {
      const fixture = new Fixture(new ScriptedEventStream([]), midGame);

      fixture.engine.connect();
      await Promise.resolve();
      await Promise.resolve();

      expect(fixture.api.snapshots).toBe(1);
      expect(fixture.canvas.calls.length).toBeGreaterThan(0);
      expect(fixture.playerList.shown.map((player) => player.name)).toEqual(["one"]);
    });

    it("leaves the start button disabled while that game is still running", async () => {
      const fixture = new Fixture(new ScriptedEventStream([]), midGame);

      fixture.engine.connect();
      await Promise.resolve();
      await Promise.resolve();

      expect(fixture.startButton.enabled).toBe(false);
    });

    it("keeps the button usable when nothing is playing", async () => {
      const fixture = new Fixture(new ScriptedEventStream([]));

      fixture.engine.connect();
      await Promise.resolve();
      await Promise.resolve();

      expect(fixture.startButton.enabled).toBe(true);
    });
  });
});
