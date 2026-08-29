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
  strokeLine(from: Position, to: Position, color: string, lineWidth?: number): void;
  fillCircle(centre: Position, radius: number, color: string): void;
  strokeCircle(centre: Position, radius: number, color: string, lineWidth?: number): void;
  drawSprite(sprite: number, centre: Position, size: number, opacity?: number): void;
  fillPolygon(points: readonly Position[], color: string): void;
  strokePolygon(points: readonly Position[], color: string, lineWidth?: number): void;
  fillEllipse(centre: Position, radiusX: number, radiusY: number, color: string): void;
  strokeEllipse(
    centre: Position,
    radiusX: number,
    radiusY: number,
    color: string,
    lineWidth?: number,
  ): void;
  drawText(
    text: string,
    centre: Position,
    font: string,
    color: string,
    align?: "left" | "center" | "right",
  ): void;
}
