import type { Position } from "../game/index.js";

/**
 * Drawing primitives, not a canvas element. Edge module.
 *
 * Deliberately smaller than the real 2D context: a renderer that can only do these four things is
 * one a test can assert on exactly.
 */
export interface Canvas {
  readonly width: number;
  readonly height: number;
  clear(): void;
  strokeLine(from: Position, to: Position, color: string): void;
  fillCircle(centre: Position, radius: number, color: string): void;
  drawSprite(sprite: number, centre: Position, size: number): void;
}
