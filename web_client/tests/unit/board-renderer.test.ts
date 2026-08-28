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

  it("draws 3D slab faces and diamond tiles for the board", () => {
    const canvas = new RecordingCanvas(400, 300);

    new BoardRenderer(canvas).render(state({ board: { width: 4, height: 2 } }));

    // 1 slab ground shadow + 2 slab face polygons (left and right) + 4x2 = 8 tile polygons
    expect(canvas.polygons()).toHaveLength(1 + 2 + 8);
    // 2 slab borders + 8 tile borders + 1 perimeter border
    expect(canvas.strokePolygons()).toHaveLength(2 + 8 + 1);
    // 1 slab vertical crease line
    expect(canvas.lines()).toHaveLength(1);
  });

  it("renders player tile highlight, shadow ellipse, and standing character sprite", () => {
    const canvas = new RecordingCanvas(400, 400);

    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        players: [
          { name: "one", position: { x: 0, y: 0 }, color: "#4c8dff", sprite: 2, reasoning: "" },
        ],
      }),
    );

    // 1 shadow ellipse on the player's square
    const ellipses = canvas.ellipses();
    expect(ellipses).toHaveLength(1);
    expect(ellipses[0]?.color).toBe("rgba(0, 0, 0, 0.55)");

    // 1 sprite drawn standing upright above the shadow/tile center
    const sprites = canvas.sprites();
    expect(sprites).toHaveLength(1);
    expect(sprites[0]?.sprite).toBe(2);

    const shadow = ellipses[0]!;
    const sprite = sprites[0]!;
    // Horizontal center matches tile/shadow center
    expect(sprite.centre.x).toBeCloseTo(shadow.centre.x, 2);
    // Sprite center is elevated above the shadow (standing upright on the square)
    expect(sprite.centre.y).toBeLessThan(shadow.centre.y);
  });

  it("depth-sorts players so characters in front render on top of characters behind", () => {
    const canvas = new RecordingCanvas(400, 400);

    // Provide player at (5, 5) first, then player at (0, 0)
    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        players: [
          { name: "front", position: { x: 5, y: 5 }, color: "#ff5d7a", sprite: 1, reasoning: "" },
          { name: "back", position: { x: 0, y: 0 }, color: "#4c8dff", sprite: 0, reasoning: "" },
        ],
      }),
    );

    const sprites = canvas.sprites();
    expect(sprites).toHaveLength(2);
    // Back player (0, 0) rendered first, front player (5, 5) rendered second
    expect(sprites[0]?.sprite).toBe(0);
    expect(sprites[1]?.sprite).toBe(1);
  });

  it("clears before every frame", () => {
    const canvas = new RecordingCanvas();
    const renderer = new BoardRenderer(canvas);

    renderer.render(state());
    renderer.render(state());

    expect(canvas.calls.filter((call) => call.kind === "clear")).toHaveLength(2);
  });
});
