import type { Canvas } from "../../interfaces/canvas/index.js";
import type { Position } from "../../interfaces/game/index.js";

/** Edge module. The only code that touches a real 2D context. */
export class Html5Canvas implements Canvas {
  constructor(
    private readonly element: HTMLCanvasElement,
    private readonly context: CanvasRenderingContext2D
  ) {}

  get width(): number {
    return this.element.width;
  }

  get height(): number {
    return this.element.height;
  }

  clear(): void {
    this.context.clearRect(0, 0, this.width, this.height);
  }

  strokeLine(from: Position, to: Position, color: string): void {
    this.context.strokeStyle = color;
    this.context.lineWidth = 1;
    this.context.beginPath();
    // Half-pixel offset, or a 1px line straddles two device pixels and blurs.
    this.context.moveTo(Math.round(from.x) + 0.5, Math.round(from.y) + 0.5);
    this.context.lineTo(Math.round(to.x) + 0.5, Math.round(to.y) + 0.5);
    this.context.stroke();
  }

  fillCircle(centre: Position, radius: number, color: string): void {
    this.context.fillStyle = color;
    this.context.beginPath();
    this.context.arc(centre.x, centre.y, radius, 0, Math.PI * 2);
    this.context.fill();
  }
}
