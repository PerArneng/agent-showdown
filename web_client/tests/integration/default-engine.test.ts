import { beforeEach, describe, expect, it } from "vitest";
import demoGame from "../../fixtures/demo-game.json" with { type: "json" };
import type { GameEvent } from "../../src/interfaces/game/index.js";
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
  readonly api = new RecordingGameApi();
  readonly playerList = new InMemoryPlayerList();
  readonly statusText = new InMemoryStatusText();
  readonly startButton = new InMemoryStartButton();
  readonly connectionIndicator = new InMemoryConnectionIndicator();
  readonly engine: DefaultEngine;

  constructor(readonly stream: ScriptedEventStream) {
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
});
