import type { Position } from "./position.js";

/** In-flight visual animation effect rendered over the board. */
export type VisualEffect =
  | {
      readonly type: "move";
      readonly player: string;
      readonly from: Position;
      readonly to: Position;
      readonly progress: number;
    }
  | {
      readonly type: "fireball";
      readonly from: Position;
      readonly to: Position;
      readonly progress: number;
    }
  | {
      readonly type: "explosion";
      readonly position: Position;
      readonly progress: number;
    };
