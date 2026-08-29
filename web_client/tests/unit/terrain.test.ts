import { describe, expect, it } from "vitest";
import { Terrain } from "../../src/modules/game/terrain.js";

describe("Terrain", () => {
  const terrain = new Terrain();

  it("calculates deterministic and continuous heights", () => {
    const h1 = terrain.getHeight(0, 0);
    const h2 = terrain.getHeight(0, 0);
    expect(h1).toBe(h2);

    // Height should be smooth and bounded within gentle mounds (< 0.2 units)
    expect(Math.abs(h1)).toBeLessThan(0.2);

    const hClose = terrain.getHeight(0.01, 0.01);
    expect(Math.abs(hClose - h1)).toBeLessThan(0.01);
  });

  it("calculates unit-length surface normals", () => {
    const normal = terrain.getNormal(2.5, -1.8);
    const length = Math.sqrt(normal.nx * normal.nx + normal.ny * normal.ny + normal.nz * normal.nz);
    expect(length).toBeCloseTo(1.0, 5);
    expect(normal.ny).toBeGreaterThan(0.9); // Mostly pointing upwards
  });

  it("maps grid coordinates to centered world coordinates", () => {
    const center = terrain.gridToWorld(4.5, 4.5, 10, 10);
    expect(center.x).toBeCloseTo(0, 5);
    expect(center.z).toBeCloseTo(0, 5);

    const corner = terrain.gridToWorld(0, 0, 10, 10);
    expect(corner.x).toBeCloseTo(-4.5, 5);
    expect(corner.z).toBeCloseTo(-4.5, 5);

    const grid = terrain.worldToGrid(corner.x, corner.z, 10, 10);
    expect(grid.gx).toBeCloseTo(0, 5);
    expect(grid.gy).toBeCloseTo(0, 5);
  });

  it("computes accurate world bounds", () => {
    const bounds = terrain.getWorldBounds(10, 10);
    expect(bounds.minX).toBe(-5);
    expect(bounds.maxX).toBe(5);
    expect(bounds.minZ).toBe(-5);
    expect(bounds.maxZ).toBe(5);
  });
});
