import type { Canvas } from "../../interfaces/canvas/index.js";
import type { Board, ClientState, Position, Renderer } from "../../interfaces/game/index.js";

const TILE_COLOR_EVEN = "#1d222c";
const TILE_COLOR_ODD = "#242b38";
const GRID_BORDER_COLOR = "#323c4e";
const BOARD_OUTLINE_COLOR = "#45526b";

const SLAB_SHADOW_COLOR = "rgba(0, 0, 0, 0.35)";
const SLAB_LEFT_COLOR = "#14171f";
const SLAB_LEFT_BORDER = "#232936";
const SLAB_RIGHT_COLOR = "#1a1f2a";
const SLAB_RIGHT_BORDER = "#2b3343";
const SLAB_CREASE_COLOR = "#3d485e";

const SHADOW_COLOR = "rgba(0, 0, 0, 0.55)";
const SHADOW_RADIUS_RATIO = 0.52;
const SPRITE_SIZE_RATIO = 1.85;
const SPRITE_VERTICAL_ANCHOR_RATIO = 0.38;

interface IsometricProjection {
  readonly tileWidthHalf: number;
  readonly tileHeightHalf: number;
  readonly slabThickness: number;
  readonly spriteSize: number;
  project(gx: number, gy: number): Position;
  tileCorners(x: number, y: number): readonly [Position, Position, Position, Position];
  tileCentre(x: number, y: number): Position;
}

/** Turns state into isometric drawing calls. Knows the canvas contract and nothing else. */
export class BoardRenderer implements Renderer {
  constructor(private readonly canvas: Canvas) {}

  render(state: ClientState): void {
    this.canvas.clear();
    if (state.board === null) {
      return;
    }

    const proj = this.createProjection(state.board);

    this.renderSlab(state.board, proj);
    this.renderTiles(state.board, proj);
    this.renderPlayers(state, proj);
  }

  private createProjection(board: Board): IsometricProjection {
    const totalUnits = board.width + board.height;
    const tileWidthHalf = Math.min(
      (this.canvas.width - 40) / totalUnits,
      (this.canvas.height - 60) / (totalUnits * 0.5 + 1.2),
    );
    const tileHeightHalf = tileWidthHalf * 0.5;
    const slabThickness = Math.max(12, Math.round(tileHeightHalf * 0.8));
    const spriteSize = Math.round(tileWidthHalf * SPRITE_SIZE_RATIO);

    const originX = this.canvas.width / 2 - ((board.width - board.height) * tileWidthHalf) / 2;
    const originY =
      (this.canvas.height - (totalUnits * tileHeightHalf + slabThickness)) / 2 +
      tileWidthHalf * 0.35;

    const project = (gx: number, gy: number): Position => ({
      x: originX + (gx - gy) * tileWidthHalf,
      y: originY + (gx + gy) * tileHeightHalf,
    });

    const tileCorners = (
      x: number,
      y: number,
    ): readonly [Position, Position, Position, Position] => [
      project(x, y),
      project(x + 1, y),
      project(x + 1, y + 1),
      project(x, y + 1),
    ];

    const tileCentre = (x: number, y: number): Position => project(x + 0.5, y + 0.5);

    return {
      tileWidthHalf,
      tileHeightHalf,
      slabThickness,
      spriteSize,
      project,
      tileCorners,
      tileCentre,
    };
  }

  private renderSlab(board: Board, proj: IsometricProjection): void {
    const top = proj.project(0, 0);
    const left = proj.project(0, board.height);
    const bottom = proj.project(board.width, board.height);
    const right = proj.project(board.width, 0);

    const leftBottom = { x: left.x, y: left.y + proj.slabThickness };
    const bottomBottom = { x: bottom.x, y: bottom.y + proj.slabThickness };
    const rightBottom = { x: right.x, y: right.y + proj.slabThickness };

    // Soft drop shadow under the entire extruded board slab
    const slabShadow: readonly Position[] = [
      { x: top.x, y: top.y + proj.slabThickness + 4 },
      { x: right.x + 8, y: right.y + proj.slabThickness + 4 },
      { x: bottomBottom.x, y: bottomBottom.y + 12 },
      { x: left.x - 8, y: left.y + proj.slabThickness + 4 },
    ];
    this.canvas.fillPolygon(slabShadow, SLAB_SHADOW_COLOR);

    // Left slab face (shadow side)
    const leftFace: readonly Position[] = [left, bottom, bottomBottom, leftBottom];
    this.canvas.fillPolygon(leftFace, SLAB_LEFT_COLOR);
    this.canvas.strokePolygon(leftFace, SLAB_LEFT_BORDER, 1);

    // Right slab face (lighted side)
    const rightFace: readonly Position[] = [bottom, right, rightBottom, bottomBottom];
    this.canvas.fillPolygon(rightFace, SLAB_RIGHT_COLOR);
    this.canvas.strokePolygon(rightFace, SLAB_RIGHT_BORDER, 1);

    // Front vertical crease
    this.canvas.strokeLine(bottom, bottomBottom, SLAB_CREASE_COLOR, 1.5);
  }

  private renderTiles(board: Board, proj: IsometricProjection): void {
    for (let y = 0; y < board.height; y++) {
      for (let x = 0; x < board.width; x++) {
        const corners = proj.tileCorners(x, y);
        const color = (x + y) % 2 === 0 ? TILE_COLOR_EVEN : TILE_COLOR_ODD;
        this.canvas.fillPolygon(corners, color);
        this.canvas.strokePolygon(corners, GRID_BORDER_COLOR, 1);
      }
    }

    // Outer board perimeter outline
    const perimeter: readonly Position[] = [
      proj.project(0, 0),
      proj.project(board.width, 0),
      proj.project(board.width, board.height),
      proj.project(0, board.height),
    ];
    this.canvas.strokePolygon(perimeter, BOARD_OUTLINE_COLOR, 1.5);
  }

  private renderPlayers(state: ClientState, proj: IsometricProjection): void {
    // Sort from back to front (lowest to highest x+y) for correct isometric depth overlap
    const sortedPlayers = [...state.players].sort(
      (a, b) => a.position.x + a.position.y - (b.position.x + b.position.y),
    );

    for (const player of sortedPlayers) {
      const corners = proj.tileCorners(player.position.x, player.position.y);
      const centre = proj.tileCentre(player.position.x, player.position.y);

      // Player-colored tile highlight
      this.canvas.fillPolygon(corners, `${player.color}35`);
      this.canvas.strokePolygon(corners, `${player.color}dd`, 2);

      // Soft ground shadow on the square
      this.canvas.fillEllipse(
        centre,
        proj.tileWidthHalf * SHADOW_RADIUS_RATIO,
        proj.tileHeightHalf * SHADOW_RADIUS_RATIO,
        SHADOW_COLOR,
      );

      // Standing sprite upright on top of the square
      const spriteCentre: Position = {
        x: centre.x,
        y: centre.y - proj.spriteSize * SPRITE_VERTICAL_ANCHOR_RATIO,
      };
      this.canvas.drawSprite(player.sprite, spriteCentre, proj.spriteSize);
    }
  }
}
