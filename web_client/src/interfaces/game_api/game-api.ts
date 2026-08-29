import type { GameSnapshot } from "../game/index.js";

/** Asking the server for a fresh match. Edge: the live implementation posts over HTTP. */
export interface GameApi {
  newGame(): Promise<void>;
  /** The current game, for a client that connected after it started. */
  fetchSnapshot(): Promise<GameSnapshot>;
}
