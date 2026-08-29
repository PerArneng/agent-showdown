import { describe, expect, it } from "vitest";
import {
  createObstacleMesh,
  obstacleRadius,
  type WallNeighbors,
} from "../../src/modules/game/obstacle-meshes.js";
import { ModelLoader } from "../../src/modules/game/model-loader.js";

const loader = new ModelLoader();

describe("createObstacleMesh", () => {
  it("builds a group for every kind of terrain", () => {
    for (const kind of ["tree", "boulder", "stone_wall", "stone_well"] as const) {
      const mesh = createObstacleMesh(kind, 7, loader);
      expect(mesh.children.length).toBeGreaterThan(0);
    }
  });

  it("grows the same tree on the same square every time", () => {
    const first = createObstacleMesh("tree", 42, loader);
    const second = createObstacleMesh("tree", 42, loader);

    expect(second.rotation.y).toEqual(first.rotation.y);
    expect(second.scale.x).toEqual(first.scale.x);
  });

  it("grows the same boulder on the same square every time", () => {
    const first = createObstacleMesh("boulder", 42, loader);
    const second = createObstacleMesh("boulder", 42, loader);

    expect(second.rotation.y).toEqual(first.rotation.y);
    expect(second.scale.x).toEqual(first.scale.x);
  });

  it("grows different variations on different squares", () => {
    const a = createObstacleMesh("boulder", 1, loader);
    const b = createObstacleMesh("boulder", 2, loader);

    expect(a.rotation.y).not.toEqual(b.rotation.y);
  });

  it("rotates stone wells randomly per square seed", () => {
    const a = createObstacleMesh("stone_well", 1, loader);
    const b = createObstacleMesh("stone_well", 2, loader);

    expect(a.rotation.y).not.toEqual(b.rotation.y);
  });

  it("fits a wall to exactly one tile, because that is how the models are authored", () => {
    // Measured through the GLB node hierarchy, every wall arm reaches 0.5 from the centre.
    const wall = createObstacleMesh("stone_wall", 10, loader);
    expect(wall.scale.toArray()).toEqual([1, 1, 1]);
  });

  describe("wall auto-tiling and orientation", () => {
    // Native arm directions, measured out of the GLBs through their node hierarchy:
    //   middle E-W | 2way W+S | 3way E,W,S (open north) | 4way all four.
    const QUARTER = Math.PI / 2;

    function wall(neighbors: WallNeighbors) {
      return createObstacleMesh("stone_wall", 1, loader, neighbors);
    }

    it("uses the cross where the wall crosses", () => {
      const cross = wall({ north: true, south: true, west: true, east: true });
      expect(cross.userData.modelKey).toBe("stone-wall-4way");
      expect(cross.rotation.y).toBe(0);
    });

    it("turns the T's open side to wherever the wall does not continue", () => {
      for (const [neighbors, rotation] of [
        [{ south: true, west: true, east: true }, 0], // open north
        [{ north: true, south: true, west: true }, -QUARTER], // open east
        [{ north: true, west: true, east: true }, Math.PI], // open south
        [{ north: true, south: true, east: true }, QUARTER], // open west
      ] as const) {
        const piece = wall(neighbors);
        expect(piece.userData.modelKey).toBe("stone-wall-3way");
        expect(piece.rotation.y).toBeCloseTo(rotation);
      }
    });

    it("lays a straight run along its own axis", () => {
      const we = wall({ west: true, east: true });
      expect(we.userData.modelKey).toBe("stone-wall-middle");
      expect(we.rotation.y).toBe(0); // The model already runs east-west.

      const ns = wall({ north: true, south: true });
      expect(ns.userData.modelKey).toBe("stone-wall-middle");
      expect(ns.rotation.y).toBeCloseTo(QUARTER);
    });

    it("turns the corner piece to the two sides the wall actually continues on", () => {
      for (const [neighbors, rotation] of [
        [{ west: true, south: true }, 0], // the model's native arms
        [{ north: true, west: true }, -QUARTER],
        [{ north: true, east: true }, Math.PI],
        [{ east: true, south: true }, QUARTER],
      ] as const) {
        const piece = wall(neighbors);
        expect(piece.userData.modelKey).toBe("stone-wall-2way");
        expect(piece.rotation.y).toBeCloseTo(rotation);
      }
    });

    it("fills a stub's square with a straight, flush with the open edge", () => {
      for (const [neighbors, rotation] of [
        [{ north: true }, QUARTER],
        [{ south: true }, QUARTER],
        [{ east: true }, 0],
        [{ west: true }, 0],
      ] as const) {
        const piece = wall(neighbors);
        expect(piece.userData.modelKey).toBe("stone-wall-middle");
        expect(piece.rotation.y).toBeCloseTo(rotation);
      }
    });

    it("leaves a lone wall as a lump, which reaches no edge to join to", () => {
      const isolated = wall({});
      expect(isolated.userData.modelKey).toBe("stone-wall-end");
      expect([0, Math.PI / 2]).toContain(isolated.rotation.y);
    });
  });

  describe("obstacleRadius", () => {
    it("defines radii for all terrain kinds", () => {
      expect(obstacleRadius("tree")).toBe(0.7);
      expect(obstacleRadius("stone_wall")).toBe(0.65);
      expect(obstacleRadius("stone_well")).toBe(0.65);
      expect(obstacleRadius("boulder")).toBe(0.55);
    });
  });
});
