import type { SpritePicker } from "../../interfaces/game/index.js";

const SPRITE_COUNT = 10;

/**
 * Hashes agent names to sprite indices (0..9) with linear probing to avoid collisions.
 * Pure and deterministic.
 */
export class HashSpritePicker implements SpritePicker {
  pick(name: string, taken: readonly number[]): number {
    const hash = this.hash(name);
    const takenSet = new Set(taken);
    for (let offset = 0; offset < SPRITE_COUNT; offset++) {
      const candidate = (hash + offset) % SPRITE_COUNT;
      if (!takenSet.has(candidate)) {
        return candidate;
      }
    }
    return hash;
  }

  private hash(name: string): number {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = ((hash << 5) - hash + name.charCodeAt(i)) | 0;
    }
    return Math.abs(hash) % SPRITE_COUNT;
  }
}
