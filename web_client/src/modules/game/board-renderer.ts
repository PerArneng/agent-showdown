import type { Canvas } from "../../interfaces/canvas/index.js";
import type { Board, ClientState, Position, Renderer } from "../../interfaces/game/index.js";

const TILE_COLOR_EVEN = "#4cae4f";
const TILE_COLOR_ODD = "#3e9642";
const GRID_BORDER_COLOR = "#2f7832";
const BOARD_OUTLINE_COLOR = "#1f5422";

const SLAB_SHADOW_COLOR = "rgba(0, 0, 0, 0.40)";
const SLAB_LEFT_COLOR = "#3d261a";
const SLAB_LEFT_BORDER = "#281810";
const SLAB_RIGHT_COLOR = "#583928";
const SLAB_RIGHT_BORDER = "#3c251a";
const SLAB_CREASE_COLOR = "#6e4933";

const SHADOW_COLOR = "rgba(0, 0, 0, 0.55)";
const SHADOW_RADIUS_RATIO = 0.52;
const SPRITE_SIZE_RATIO = 1.85;
const SPRITE_VERTICAL_ANCHOR_RATIO = 0.38;

const RUNES = ["᚛", "ᚱ", "ᛟ", "ᚦ", "ᛉ", "ᛋ", "✦", "◈"] as const;

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
    this.renderEffects(state, proj);
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
      const isDead = player.health <= 0;
      const isThinking = !isDead && state.thinking === player.name;

      // Handle smooth movement interpolation
      let gx = player.position.x;
      let gy = player.position.y;
      if (state.effect?.type === "move" && state.effect.player === player.name) {
        gx =
          state.effect.from.x + (state.effect.to.x - state.effect.from.x) * state.effect.progress;
        gy =
          state.effect.from.y + (state.effect.to.y - state.effect.from.y) * state.effect.progress;
      }

      const centre = proj.project(gx + 0.5, gy + 0.5);
      const corners = proj.tileCorners(Math.round(gx), Math.round(gy));

      // Player-colored tile highlight (brighter and prominent border when thinking)
      if (!isDead) {
        const fillColor = isThinking ? `${player.color}66` : `${player.color}35`;
        const strokeColor = isThinking ? "#ffffff" : `${player.color}dd`;
        const strokeWidth = isThinking ? 3 : 2;

        this.canvas.fillPolygon(corners, fillColor);
        this.canvas.strokePolygon(corners, strokeColor, strokeWidth);
      }

      // Active Turn Magical Rune Ring circling the player on ground plane
      if (isThinking) {
        // Outer glowing rune ring
        this.canvas.strokeEllipse(
          centre,
          proj.tileWidthHalf * 1.05,
          proj.tileHeightHalf * 1.05,
          "rgba(255, 215, 0, 0.85)",
          2,
        );

        // Inner glowing resonance ring
        this.canvas.strokeEllipse(
          centre,
          proj.tileWidthHalf * 0.72,
          proj.tileHeightHalf * 0.72,
          "rgba(76, 141, 255, 0.75)",
          1.5,
        );

        // Ethereal magic energy disc
        this.canvas.fillEllipse(
          centre,
          proj.tileWidthHalf * 1.05,
          proj.tileHeightHalf * 1.05,
          "rgba(130, 80, 255, 0.18)",
        );

        // Ancient rune glyphs positioned around the isometric perimeter
        for (let i = 0; i < 8; i++) {
          const angle = (i * Math.PI) / 4;
          const rx = centre.x + Math.cos(angle) * proj.tileWidthHalf * 0.88;
          const ry = centre.y + Math.sin(angle) * proj.tileHeightHalf * 0.88;
          this.canvas.fillCircle({ x: rx, y: ry }, 2, "#ffd700");
          this.canvas.drawText(
            RUNES[i] ?? "✦",
            { x: rx, y: ry },
            "9px monospace",
            "rgba(255, 255, 255, 0.9)",
          );
        }

        // Radiant energy aura under the sprite
        this.canvas.fillEllipse(
          centre,
          proj.tileWidthHalf * 0.75,
          proj.tileHeightHalf * 0.75,
          "rgba(255, 215, 0, 0.35)",
        );
      }

      // Ground shadow on the square
      if (!isDead) {
        this.canvas.fillEllipse(
          centre,
          proj.tileWidthHalf * SHADOW_RADIUS_RATIO,
          proj.tileHeightHalf * SHADOW_RADIUS_RATIO,
          SHADOW_COLOR,
        );
      } else {
        // Defeated / depleted subtle dark residue
        this.canvas.fillEllipse(
          centre,
          proj.tileWidthHalf * SHADOW_RADIUS_RATIO * 0.7,
          proj.tileHeightHalf * SHADOW_RADIUS_RATIO * 0.7,
          "rgba(0, 0, 0, 0.3)",
        );
      }

      // Standing sprite upright on top of the square (reduced opacity for defeated robots)
      const spriteCentre: Position = {
        x: centre.x,
        y: centre.y - proj.spriteSize * SPRITE_VERTICAL_ANCHOR_RATIO,
      };
      this.canvas.drawSprite(player.sprite, spriteCentre, proj.spriteSize, isDead ? 0.35 : 1);

      // Mini Health Bar & Indicators
      if (isDead) {
        // Skull indicator over defeated robot
        this.canvas.drawText(
          "💀",
          { x: spriteCentre.x, y: spriteCentre.y - proj.spriteSize * 0.46 },
          "14px sans-serif",
          "#ef4444",
        );
      } else {
        // Floating mini health bar
        const barWidth = Math.max(24, Math.round(proj.spriteSize * 0.65));
        const barHeight = 4;
        const barX = spriteCentre.x - barWidth / 2;
        const barY = spriteCentre.y - proj.spriteSize * 0.52;
        const healthRatio = Math.max(0, Math.min(1, player.health / 100));

        // Health bar track
        this.canvas.fillPolygon(
          [
            { x: barX - 1, y: barY - 1 },
            { x: barX + barWidth + 1, y: barY - 1 },
            { x: barX + barWidth + 1, y: barY + barHeight + 1 },
            { x: barX - 1, y: barY + barHeight + 1 },
          ],
          "rgba(0, 0, 0, 0.75)",
        );

        // Health bar fill
        const fillWidth = Math.round(barWidth * healthRatio);
        if (fillWidth > 0) {
          const hpColor =
            healthRatio > 0.5 ? "#22c55e" : healthRatio > 0.25 ? "#eab308" : "#ef4444";
          this.canvas.fillPolygon(
            [
              { x: barX, y: barY },
              { x: barX + fillWidth, y: barY },
              { x: barX + fillWidth, y: barY + barHeight },
              { x: barX, y: barY + barHeight },
            ],
            hpColor,
          );
        }

        // Floating thought beacon above active player's head
        if (isThinking) {
          const beaconCentre: Position = {
            x: spriteCentre.x,
            y: barY - 8,
          };
          this.canvas.fillCircle(beaconCentre, Math.max(3, proj.spriteSize * 0.1), "#ffd700");
          this.canvas.fillCircle(beaconCentre, Math.max(1.5, proj.spriteSize * 0.05), "#ffffff");
        }
      }
    }
  }

  private renderEffects(state: ClientState, proj: IsometricProjection): void {
    if (!state.effect) {
      return;
    }

    if (state.effect.type === "fireball") {
      const from = state.effect.from;
      const to = state.effect.to;
      const p = state.effect.progress;
      const gx = from.x + (to.x - from.x) * p;
      const gy = from.y + (to.y - from.y) * p;
      const groundPos = proj.project(gx + 0.5, gy + 0.5);
      const flightPos: Position = {
        x: groundPos.x,
        y: groundPos.y - proj.tileHeightHalf * 1.4,
      };

      // Fiery ground shadow
      this.canvas.fillEllipse(
        groundPos,
        proj.tileWidthHalf * 0.28,
        proj.tileHeightHalf * 0.28,
        "rgba(255, 100, 0, 0.35)",
      );

      // Fiery spark trail behind projectile
      for (let i = 1; i <= 3; i++) {
        const trailP = Math.max(0, p - i * 0.12);
        const tgx = from.x + (to.x - from.x) * trailP;
        const tgy = from.y + (to.y - from.y) * trailP;
        const tGround = proj.project(tgx + 0.5, tgy + 0.5);
        const tFlight: Position = {
          x: tGround.x,
          y: tGround.y - proj.tileHeightHalf * 1.4,
        };
        this.canvas.fillCircle(
          tFlight,
          Math.max(2, proj.tileWidthHalf * 0.12 * (1 - i * 0.25)),
          "rgba(255, 120, 0, 0.6)",
        );
      }

      // Outer fireball glow
      this.canvas.fillCircle(
        flightPos,
        Math.max(8, proj.tileWidthHalf * 0.36),
        "rgba(255, 80, 0, 0.45)",
      );
      // Mid flame
      this.canvas.fillCircle(flightPos, Math.max(5, proj.tileWidthHalf * 0.22), "#ff6b1a");
      // Core ember
      this.canvas.fillCircle(flightPos, Math.max(2.5, proj.tileWidthHalf * 0.11), "#fff7a0");
    } else if (state.effect.type === "explosion") {
      const pos = state.effect.position;
      const p = state.effect.progress;
      const centre = proj.tileCentre(pos.x, pos.y);
      const elevated: Position = { x: centre.x, y: centre.y - proj.spriteSize * 0.3 };

      // Expanding ground shockwave ring
      const shockR = proj.tileWidthHalf * (0.4 + p * 0.9);
      this.canvas.strokeEllipse(
        centre,
        shockR,
        shockR * 0.5,
        `rgba(255, 120, 0, ${Math.max(0, 1 - p)})`,
        3,
      );

      // Fiery blast burst
      const burstR = proj.tileWidthHalf * (0.3 + p * 0.6);
      this.canvas.fillCircle(elevated, burstR, `rgba(255, 80, 0, ${Math.max(0, 0.8 * (1 - p))})`);
      this.canvas.fillCircle(
        elevated,
        burstR * 0.6,
        `rgba(255, 200, 50, ${Math.max(0, 0.9 * (1 - p))})`,
      );
      this.canvas.fillCircle(elevated, burstR * 0.3, `rgba(255, 255, 255, ${Math.max(0, 1 - p)})`);
    }
  }
}
