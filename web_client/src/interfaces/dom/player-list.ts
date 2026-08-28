import type { PlayerState } from "../game/index.js";

/** The roster in the sidebar. Edge module: the real one writes to the document. */
export interface PlayerList {
  show(players: readonly PlayerState[]): void;
}
