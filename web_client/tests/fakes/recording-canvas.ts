import type { Canvas } from "../../src/interfaces/canvas/index.js";
import type { Position } from "../../src/interfaces/game/index.js";

export type DrawCall =
  | { readonly kind: "clear" }
  | { readonly kind: "line"; readonly from: Position; readonly to: Position; readonly color: string }
  | {
      readonly kind: "circle";
      readonly centre: Position;
      readonly radius: number;
      readonly color: string;
    };

/** Test fake. Records what it was asked to draw instead of drawing it. */
export class RecordingCanvas implements Canvas {
  readonly calls: DrawCall[] = [];

  constructor(
    readonly width = 100,
    readonly height = 100
  ) {}

  clear(): void {
    this.calls.push({ kind: "clear" });
  }

  strokeLine(from: Position, to: Position, color: string): void {
    this.calls.push({ kind: "line", from, to, color });
  }

  fillCircle(centre: Position, radius: number, color: string): void {
    this.calls.push({ kind: "circle", centre, radius, color });
  }

  circles(): readonly DrawCall[] {
    return this.calls.filter((call) => call.kind === "circle");
  }
}
