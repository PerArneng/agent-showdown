import type { Canvas } from "../../src/interfaces/canvas/index.js";
import type { Position } from "../../src/interfaces/game/index.js";

export type DrawCall =
  | { readonly kind: "clear" }
  | {
      readonly kind: "line";
      readonly from: Position;
      readonly to: Position;
      readonly color: string;
      readonly lineWidth?: number | undefined;
    }
  | {
      readonly kind: "circle";
      readonly centre: Position;
      readonly radius: number;
      readonly color: string;
    }
  | {
      readonly kind: "strokeCircle";
      readonly centre: Position;
      readonly radius: number;
      readonly color: string;
      readonly lineWidth?: number | undefined;
    }
  | {
      readonly kind: "sprite";
      readonly sprite: number;
      readonly centre: Position;
      readonly size: number;
      readonly opacity?: number | undefined;
    }
  | {
      readonly kind: "polygon";
      readonly points: readonly Position[];
      readonly color: string;
    }
  | {
      readonly kind: "strokePolygon";
      readonly points: readonly Position[];
      readonly color: string;
      readonly lineWidth?: number | undefined;
    }
  | {
      readonly kind: "ellipse";
      readonly centre: Position;
      readonly radiusX: number;
      readonly radiusY: number;
      readonly color: string;
    }
  | {
      readonly kind: "strokeEllipse";
      readonly centre: Position;
      readonly radiusX: number;
      readonly radiusY: number;
      readonly color: string;
      readonly lineWidth?: number | undefined;
    }
  | {
      readonly kind: "text";
      readonly text: string;
      readonly centre: Position;
      readonly font: string;
      readonly color: string;
      readonly align?: "left" | "center" | "right" | undefined;
    };

/** Test fake. Records what it was asked to draw instead of drawing it. */
export class RecordingCanvas implements Canvas {
  readonly calls: DrawCall[] = [];

  constructor(
    readonly width = 100,
    readonly height = 100,
  ) {}

  clear(): void {
    this.calls.push({ kind: "clear" });
  }

  strokeLine(from: Position, to: Position, color: string, lineWidth = 1): void {
    this.calls.push({ kind: "line", from, to, color, lineWidth });
  }

  fillCircle(centre: Position, radius: number, color: string): void {
    this.calls.push({ kind: "circle", centre, radius, color });
  }

  strokeCircle(centre: Position, radius: number, color: string, lineWidth = 1): void {
    this.calls.push({ kind: "strokeCircle", centre, radius, color, lineWidth });
  }

  drawSprite(sprite: number, centre: Position, size: number, opacity?: number): void {
    this.calls.push({ kind: "sprite", sprite, centre, size, opacity });
  }

  fillPolygon(points: readonly Position[], color: string): void {
    this.calls.push({ kind: "polygon", points, color });
  }

  strokePolygon(points: readonly Position[], color: string, lineWidth = 1): void {
    this.calls.push({ kind: "strokePolygon", points, color, lineWidth });
  }

  fillEllipse(centre: Position, radiusX: number, radiusY: number, color: string): void {
    this.calls.push({ kind: "ellipse", centre, radiusX, radiusY, color });
  }

  strokeEllipse(
    centre: Position,
    radiusX: number,
    radiusY: number,
    color: string,
    lineWidth = 1,
  ): void {
    this.calls.push({ kind: "strokeEllipse", centre, radiusX, radiusY, color, lineWidth });
  }

  drawText(
    text: string,
    centre: Position,
    font: string,
    color: string,
    align?: "left" | "center" | "right",
  ): void {
    this.calls.push({ kind: "text", text, centre, font, color, align });
  }

  lines(): readonly Extract<DrawCall, { kind: "line" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "line" }> => call.kind === "line",
    );
  }

  circles(): readonly Extract<DrawCall, { kind: "circle" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "circle" }> => call.kind === "circle",
    );
  }

  strokeCircles(): readonly Extract<DrawCall, { kind: "strokeCircle" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "strokeCircle" }> => call.kind === "strokeCircle",
    );
  }

  sprites(): readonly Extract<DrawCall, { kind: "sprite" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "sprite" }> => call.kind === "sprite",
    );
  }

  polygons(): readonly Extract<DrawCall, { kind: "polygon" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "polygon" }> => call.kind === "polygon",
    );
  }

  strokePolygons(): readonly Extract<DrawCall, { kind: "strokePolygon" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "strokePolygon" }> => call.kind === "strokePolygon",
    );
  }

  ellipses(): readonly Extract<DrawCall, { kind: "ellipse" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "ellipse" }> => call.kind === "ellipse",
    );
  }

  strokeEllipses(): readonly Extract<DrawCall, { kind: "strokeEllipse" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "strokeEllipse" }> => call.kind === "strokeEllipse",
    );
  }

  texts(): readonly Extract<DrawCall, { kind: "text" }>[] {
    return this.calls.filter(
      (call): call is Extract<DrawCall, { kind: "text" }> => call.kind === "text",
    );
  }
}
