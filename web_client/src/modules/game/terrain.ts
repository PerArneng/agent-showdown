/**
 * Deterministic low-poly terrain generation and height sampling.
 * Pure mathematical functions for terrain elevation, normals, grid positioning,
 * and diorama slab mesh generation.
 */
export interface TerrainConfig {
  readonly tileWidth: number;
  readonly tileDepth: number;
  readonly slabDepth: number;
  readonly subdivisionsPerTile: number;
}

export const DEFAULT_TERRAIN_CONFIG: TerrainConfig = {
  tileWidth: 1.0,
  tileDepth: 1.0,
  slabDepth: 1.2,
  subdivisionsPerTile: 2,
};

export class Terrain {
  constructor(private readonly config: TerrainConfig = DEFAULT_TERRAIN_CONFIG) {}

  /** Continuous deterministic height function across the terrain. */
  getHeight(x: number, z: number): number {
    return (
      0.08 * Math.sin(0.7 * x + 0.3 * z) +
      0.05 * Math.cos(0.5 * x - 0.8 * z) +
      0.03 * Math.sin(1.2 * x + 1.1 * z)
    );
  }

  /** Surface normal at world coordinate (x, z). */
  getNormal(x: number, z: number): { nx: number; ny: number; nz: number } {
    const dx =
      0.08 * 0.7 * Math.cos(0.7 * x + 0.3 * z) -
      0.05 * 0.5 * Math.sin(0.5 * x - 0.8 * z) +
      0.03 * 1.2 * Math.cos(1.2 * x + 1.1 * z);
    const dz =
      0.08 * 0.3 * Math.cos(0.7 * x + 0.3 * z) +
      0.05 * 0.8 * Math.sin(0.5 * x - 0.8 * z) +
      0.03 * 1.1 * Math.cos(1.2 * x + 1.1 * z);

    const length = Math.sqrt(dx * dx + 1.0 + dz * dz);
    return {
      nx: -dx / length,
      ny: 1.0 / length,
      nz: -dz / length,
    };
  }

  /** Converts board grid coordinates (gx, gy) to 3D world space (x, z). */
  gridToWorld(
    gx: number,
    gy: number,
    boardWidth: number,
    boardHeight: number,
  ): { x: number; y: number; z: number } {
    const x = (gx - (boardWidth - 1) / 2) * this.config.tileWidth;
    const z = (gy - (boardHeight - 1) / 2) * this.config.tileDepth;
    const y = this.getHeight(x, z);
    return { x, y, z };
  }

  /** Converts 3D world space (x, z) to board grid coordinates (gx, gy). */
  worldToGrid(
    x: number,
    z: number,
    boardWidth: number,
    boardHeight: number,
  ): { gx: number; gy: number } {
    const gx = x / this.config.tileWidth + (boardWidth - 1) / 2;
    const gy = z / this.config.tileDepth + (boardHeight - 1) / 2;
    return { gx, gy };
  }

  /** Returns the total world width and depth of the board. */
  getWorldBounds(
    boardWidth: number,
    boardHeight: number,
  ): { minX: number; maxX: number; minZ: number; maxZ: number } {
    const halfW = (boardWidth * this.config.tileWidth) / 2;
    const halfH = (boardHeight * this.config.tileDepth) / 2;
    return {
      minX: -halfW,
      maxX: halfW,
      minZ: -halfH,
      maxZ: halfH,
    };
  }
}
