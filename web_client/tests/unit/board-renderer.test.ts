import { describe, expect, it } from "vitest";
import type { ClientState } from "../../src/interfaces/game/index.js";
import { BoardRenderer } from "../../src/modules/game/index.js";
import { RecordingCanvas } from "../fakes/index.js";

function state(overrides: Partial<ClientState> = {}): ClientState {
  return {
    board: { width: 10, height: 10 },
    players: [],
    status: "",
    playing: false,
    ...overrides,
  };
}

describe("BoardRenderer", () => {
  it("draws nothing but a clear before the board is known", () => {
    const canvas = new RecordingCanvas();

    new BoardRenderer(canvas).render(state({ board: null }));

    expect(canvas.calls).toEqual([{ kind: "clear" }]);
  });

  it("draws one grid line per boundary, both ways", () => {
    const canvas = new RecordingCanvas(100, 100);

    new BoardRenderer(canvas).render(state({ board: { width: 4, height: 2 } }));

    // Fenceposts: a 4x2 board has 5 verticals and 3 horizontals.
    expect(canvas.calls.filter((call) => call.kind === "line")).toHaveLength(5 + 3);
  });

  it("puts a player in the middle of its cell", () => {
    const canvas = new RecordingCanvas(100, 100);

    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        players: [
          { name: "one", position: { x: 0, y: 0 }, color: "#fff", sprite: 2, reasoning: "" },
        ],
      }),
    );

    expect(canvas.circles()).toEqual([
      { kind: "circle", centre: { x: 5, y: 5 }, radius: 3.5, color: "#fff" },
    ]);
    expect(canvas.sprites()).toEqual([
      { kind: "sprite", sprite: 2, centre: { x: 5, y: 5 }, size: 8.5 },
    ]);
  });

  it("scales cells independently on a board that is not square", () => {
    const canvas = new RecordingCanvas(100, 50);

    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        players: [
          { name: "one", position: { x: 1, y: 1 }, color: "#fff", sprite: 2, reasoning: "" },
        ],
      }),
    );

    expect(canvas.circles()[0]).toMatchObject({ centre: { x: 15, y: 7.5 } });
    expect(canvas.sprites()[0]).toMatchObject({
      centre: { x: 15, y: 7.5 },
      sprite: 2,
      size: 4.25,
    });
  });

  it("clears before every frame", () => {
    const canvas = new RecordingCanvas();
    const renderer = new BoardRenderer(canvas);

    renderer.render(state());
    renderer.render(state());

    expect(canvas.calls.filter((call) => call.kind === "clear")).toHaveLength(2);
  });
});
