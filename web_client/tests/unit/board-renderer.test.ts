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
    thinking: null,
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

  it("renders player tile highlight, shadow ellipse, standing character sprite, and health bar", () => {
    const canvas = new RecordingCanvas(400, 400);

    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        players: [
          {
            name: "one",
            position: { x: 0, y: 0 },
            health: 100,
            color: "#4c8dff",
            sprite: 2,
            reasoning: "",
            thinkSeconds: 0,
            totalThinkSeconds: 0,
            turnsPlayed: 0,
            averageThinkSeconds: 0,
            eliminations: 0,
            deaths: 0,
            wins: 0,
          },
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
    expect(sprites[0]?.opacity).toBe(1);

    const shadow = ellipses[0]!;
    const sprite = sprites[0]!;
    // Horizontal center matches tile/shadow center
    expect(sprite.centre.x).toBeCloseTo(shadow.centre.x, 2);
    // Sprite center is elevated above the shadow (standing upright on the square)
    expect(sprite.centre.y).toBeLessThan(shadow.centre.y);

    // Mini health bar polygons (track + fill)
    expect(canvas.polygons().length).toBeGreaterThanOrEqual(2);
  });

  it("draws active isometric magical rune ring and runes when player is thinking", () => {
    const canvas = new RecordingCanvas(400, 400);

    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        thinking: "active-agent",
        players: [
          {
            name: "active-agent",
            position: { x: 2, y: 2 },
            health: 80,
            color: "#4c8dff",
            sprite: 3,
            reasoning: "calculating move",
            thinkSeconds: 0,
            totalThinkSeconds: 0,
            turnsPlayed: 0,
            averageThinkSeconds: 0,
            eliminations: 0,
            deaths: 0,
            wins: 0,
          },
        ],
      }),
    );

    // Concentric glowing rune rings
    const strokeEllipses = canvas.strokeEllipses();
    expect(strokeEllipses.length).toBeGreaterThanOrEqual(2);
    expect(strokeEllipses[0]?.color).toBe("rgba(255, 215, 0, 0.85)");
    expect(strokeEllipses[1]?.color).toBe("rgba(76, 141, 255, 0.75)");

    // Rune glyphs around perimeter
    const texts = canvas.texts();
    expect(texts.length).toBe(8);

    // Floating thought beacon circles (outer + inner)
    const circles = canvas.circles();
    expect(circles.some((c) => c.color === "#ffd700")).toBe(true);
    expect(circles.some((c) => c.color === "#ffffff")).toBe(true);

    // Prominent stroke on the tile
    const strokePolygons = canvas.strokePolygons();
    const playerTileStroke = strokePolygons.at(-1);
    expect(playerTileStroke?.color).toBe("#ffffff");
    expect(playerTileStroke?.lineWidth).toBe(3);
  });

  it("renders dead robots with ghost opacity and skull indicator", () => {
    const canvas = new RecordingCanvas(400, 400);

    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        players: [
          {
            name: "fallen-bot",
            position: { x: 3, y: 3 },
            health: 0,
            color: "#4c8dff",
            sprite: 4,
            reasoning: "",
            thinkSeconds: 0,
            totalThinkSeconds: 0,
            turnsPlayed: 0,
            averageThinkSeconds: 0,
            eliminations: 0,
            deaths: 1,
            wins: 0,
          },
        ],
      }),
    );

    const sprites = canvas.sprites();
    expect(sprites).toHaveLength(1);
    expect(sprites[0]?.opacity).toBe(0.35);

    const texts = canvas.texts();
    expect(texts.some((t) => t.text === "💀")).toBe(true);
  });

  it("renders in-flight fireball effects", () => {
    const canvas = new RecordingCanvas(400, 400);

    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        effect: {
          type: "fireball",
          from: { x: 0, y: 0 },
          to: { x: 3, y: 0 },
          progress: 0.5,
        },
      }),
    );

    // Fireball glows and spark circles
    const circles = canvas.circles();
    expect(circles.length).toBeGreaterThanOrEqual(4);
    expect(circles.some((c) => c.color === "#ff6b1a")).toBe(true);
    expect(circles.some((c) => c.color === "#fff7a0")).toBe(true);
  });

  it("renders hit explosion shockwave and blast burst", () => {
    const canvas = new RecordingCanvas(400, 400);

    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        effect: {
          type: "explosion",
          position: { x: 4, y: 4 },
          progress: 0.2,
        },
      }),
    );

    const strokeEllipses = canvas.strokeEllipses();
    expect(strokeEllipses.length).toBeGreaterThanOrEqual(1);

    const circles = canvas.circles();
    expect(circles.length).toBeGreaterThanOrEqual(3);
  });

  it("depth-sorts players so characters in front render on top of characters behind", () => {
    const canvas = new RecordingCanvas(400, 400);

    // Provide player at (5, 5) first, then player at (0, 0)
    new BoardRenderer(canvas).render(
      state({
        board: { width: 10, height: 10 },
        players: [
          {
            name: "front",
            position: { x: 5, y: 5 },
            health: 100,
            color: "#ff5d7a",
            sprite: 1,
            reasoning: "",
            thinkSeconds: 0,
            totalThinkSeconds: 0,
            turnsPlayed: 0,
            averageThinkSeconds: 0,
            eliminations: 0,
            deaths: 0,
            wins: 0,
          },
          {
            name: "back",
            position: { x: 0, y: 0 },
            health: 100,
            color: "#4c8dff",
            sprite: 0,
            reasoning: "",
            thinkSeconds: 0,
            totalThinkSeconds: 0,
            turnsPlayed: 0,
            averageThinkSeconds: 0,
            eliminations: 0,
            deaths: 0,
            wins: 0,
          },
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
