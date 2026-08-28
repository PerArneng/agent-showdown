import type { Canvas } from "../../interfaces/canvas/index.js";
import type { Board, ClientState, Renderer } from "../../interfaces/game/index.js";

const GRID_COLOR = "#262b35";
const PLAYER_RADIUS_RATIO = 0.3;

/** Turns state into drawing calls. Knows the canvas contract and nothing else. */
export class BoardRenderer implements Renderer {
  constructor(private readonly canvas: Canvas) {}

  render(state: ClientState): void {
    this.canvas.clear();
    if (state.board === null) {
      return;
    }
    const cell = this.cellSize(state.board);
    this.grid(state.board, cell);
    for (const player of state.players) {
      this.canvas.fillCircle(
        {
          x: (player.position.x + 0.5) * cell.x,
          y: (player.position.y + 0.5) * cell.y,
        },
        Math.min(cell.x, cell.y) * PLAYER_RADIUS_RATIO,
        player.color
      );
    }
  }

  private cellSize(board: Board): { x: number; y: number } {
    return { x: this.canvas.width / board.width, y: this.canvas.height / board.height };
  }

  private grid(board: Board, cell: { x: number; y: number }): void {
    for (let column = 0; column <= board.width; column++) {
      const x = column * cell.x;
      this.canvas.strokeLine({ x, y: 0 }, { x, y: this.canvas.height }, GRID_COLOR);
    }
    for (let row = 0; row <= board.height; row++) {
      const y = row * cell.y;
      this.canvas.strokeLine({ x: 0, y }, { x: this.canvas.width, y }, GRID_COLOR);
    }
  }
}
