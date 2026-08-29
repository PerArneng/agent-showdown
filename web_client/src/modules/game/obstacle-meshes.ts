import * as THREE from "three";
import type { TerrainKind } from "../../interfaces/game/index.js";
import { ModelLoader, type ModelKey } from "./model-loader.js";

/** Adjacent squares that also contain a wall, for picking junctions, corners, and ends. */
export interface WallNeighbors {
  readonly north?: boolean;
  readonly south?: boolean;
  readonly west?: boolean;
  readonly east?: boolean;
}

/**
 * Builds the 3D model that stands on an obstructed square.
 *
 * - Trees and boulders randomly pick one of two GLB variants.
 * - Stone walls pick the matching junction model and orientation (4-way, 3-way, 2-way corner,
 *   2-way straight middle, or 1-way / isolated end) based on adjacent wall neighbors,
 *   scaled to cover at most one grid tile.
 * - Stone wells instantiate the low-poly well model.
 *
 * Random choices are derived deterministically from the square seed for side-effect-free rendering.
 */
export function createObstacleMesh(
  kind: TerrainKind,
  seed: number,
  loader: ModelLoader,
  neighbors?: WallNeighbors,
): THREE.Group {
  switch (kind) {
    case "tree":
      return createTree(seed, loader);
    case "boulder":
      return createBoulder(seed, loader);
    case "stone_wall":
      return createStoneWall(seed, loader, neighbors);
    case "stone_well":
      return createStoneWell(seed, loader);
  }
}

/** How much of a tile the thing fills, for the occlusion fade that hides robots behind it. */
export function obstacleRadius(kind: TerrainKind): number {
  switch (kind) {
    case "tree":
      return 0.7;
    case "stone_wall":
      return 0.65;
    case "stone_well":
      return 0.65;
    case "boulder":
      return 0.55;
  }
}

// The wall models are authored to the tile: measured through the node hierarchy, every arm
// reaches exactly 0.5 from the centre, so a piece spans one square at scale 1 and meets its
// neighbour flush. (An earlier 3.0 came from measuring mesh-local vertices and missing the node
// transforms, which made each piece three squares long and left the wall a sprawl.)
const WALL_SCALE = 1.0;
const QUARTER = Math.PI / 2;

/** A deterministic value in [0, 1) from a seed, standing in for a random draw. */
function noise(seed: number, salt: number): number {
  const value = Math.sin(seed * 12.9898 + salt * 78.233) * 43758.5453;
  return value - Math.floor(value);
}

function createTree(seed: number, loader: ModelLoader): THREE.Group {
  const modelKey: ModelKey = noise(seed, 1) < 0.5 ? "tree-1" : "tree-2";
  const group = loader.instantiate(modelKey);
  group.scale.setScalar(0.5 + noise(seed, 2) * 0.12);
  group.rotation.y = noise(seed, 3) * Math.PI * 2;
  return group;
}

function createBoulder(seed: number, loader: ModelLoader): THREE.Group {
  const isVariant1 = noise(seed, 1) < 0.5;
  const modelKey: ModelKey = isVariant1 ? "boulder-1" : "boulder-2";
  const group = loader.instantiate(modelKey);
  const baseScale = isVariant1 ? 0.48 : 0.28;
  const scaleWobble = isVariant1 ? 0.08 : 0.05;
  group.scale.setScalar(baseScale + noise(seed, 2) * scaleWobble);
  group.rotation.y = noise(seed, 3) * Math.PI * 2;
  return group;
}

function createStoneWell(seed: number, loader: ModelLoader): THREE.Group {
  const group = loader.instantiate("stone-well");
  group.scale.setScalar(0.85);
  group.rotation.y = noise(seed, 3) * Math.PI * 2;
  return group;
}

function createStoneWall(
  seed: number,
  loader: ModelLoader,
  neighbors?: WallNeighbors,
): THREE.Group {
  const north = Boolean(neighbors?.north);
  const south = Boolean(neighbors?.south);
  const west = Boolean(neighbors?.west);
  const east = Boolean(neighbors?.east);
  const arms = Number(north) + Number(south) + Number(west) + Number(east);

  let modelKey: ModelKey;
  let rotationY: number;

  if (arms === 4) {
    modelKey = "stone-wall-4way";
    rotationY = 0;
  } else if (arms === 3) {
    // Native arms are E, W and S, so the piece is open to the north unrotated. Turn the open
    // side to wherever the wall does not continue.
    modelKey = "stone-wall-3way";
    if (!north) rotationY = 0;
    else if (!east) rotationY = -QUARTER;
    else if (!south) rotationY = Math.PI;
    else rotationY = QUARTER;
  } else if (north && south) {
    modelKey = "stone-wall-middle";
    rotationY = QUARTER; // Native arms run E-W, so a quarter turn stands it north-south.
  } else if (west && east) {
    modelKey = "stone-wall-middle";
    rotationY = 0;
  } else if (arms === 2) {
    // A corner. Native arms are W and S; each quarter turn carries W->S->E->N.
    modelKey = "stone-wall-2way";
    if (west && south) rotationY = 0;
    else if (north && west) rotationY = -QUARTER;
    else if (north && east) rotationY = Math.PI;
    else rotationY = QUARTER; // east && south
  } else if (arms === 1) {
    // A stub. The straight piece fills its square exactly, so it meets its neighbour and ends
    // flush with the tile edge on the open side.
    modelKey = "stone-wall-middle";
    rotationY = north || south ? QUARTER : 0;
  } else {
    modelKey = "stone-wall-end";
    rotationY = noise(seed, 1) < 0.5 ? 0 : QUARTER;
  }

  const group = loader.instantiate(modelKey);
  group.scale.setScalar(WALL_SCALE);
  group.rotation.y = rotationY;
  return group;
}

