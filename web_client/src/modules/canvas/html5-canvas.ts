import type { Canvas } from "../../interfaces/canvas/index.js";
import type { Position } from "../../interfaces/game/index.js";
import { SPRITE_URLS } from "./sprites.js";

/** Edge module. The only code that touches a real 2D context. */
export class Html5Canvas implements Canvas {
  private readonly spriteImages: readonly HTMLImageElement[];

  constructor(
    private readonly element: HTMLCanvasElement,
    private readonly context: CanvasRenderingContext2D,
  ) {
    this.spriteImages = SPRITE_URLS.map((url) => {
      const img = new Image();
      img.src = url;
      return img;
    });
  }

  get width(): number {
    return this.element.width;
  }

  get height(): number {
    return this.element.height;
  }

  clear(): void {
    this.context.clearRect(0, 0, this.width, this.height);
  }

  strokeLine(from: Position, to: Position, color: string, lineWidth = 1): void {
    this.context.strokeStyle = color;
    this.context.lineWidth = lineWidth;
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

  drawSprite(sprite: number, centre: Position, size: number): void {
    const index = Math.abs(sprite) % this.spriteImages.length;
    const img = this.spriteImages[index] ?? this.spriteImages[0];
    if (img === undefined) {
      return;
    }
    const half = size / 2;
    this.context.drawImage(img, centre.x - half, centre.y - half, size, size);
  }

  fillPolygon(points: readonly Position[], color: string): void {
    if (points.length === 0) {
      return;
    }
    this.context.fillStyle = color;
    this.context.beginPath();
    const first = points[0];
    if (first === undefined) {
      return;
    }
    this.context.moveTo(first.x, first.y);
    for (let i = 1; i < points.length; i++) {
      const pt = points[i];
      if (pt !== undefined) {
        this.context.lineTo(pt.x, pt.y);
      }
    }
    this.context.closePath();
    this.context.fill();
  }

  strokePolygon(points: readonly Position[], color: string, lineWidth = 1): void {
    if (points.length === 0) {
      return;
    }
    this.context.strokeStyle = color;
    this.context.lineWidth = lineWidth;
    this.context.beginPath();
    const first = points[0];
    if (first === undefined) {
      return;
    }
    this.context.moveTo(first.x, first.y);
    for (let i = 1; i < points.length; i++) {
      const pt = points[i];
      if (pt !== undefined) {
        this.context.lineTo(pt.x, pt.y);
      }
    }
    this.context.closePath();
    this.context.stroke();
  }

  fillEllipse(centre: Position, radiusX: number, radiusY: number, color: string): void {
    this.context.fillStyle = color;
    this.context.beginPath();
    this.context.ellipse(centre.x, centre.y, radiusX, radiusY, 0, 0, Math.PI * 2);
    this.context.fill();
  }
}
