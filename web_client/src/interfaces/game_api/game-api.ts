import type { GameSnapshot } from "../game/index.js";

/** Asking the server to play a game. Edge: the live implementation posts over HTTP. */
export interface GameApi {
  startGame(): Promise<void>;
  /** The current game, for a client that connected after it started. */
  fetchSnapshot(): Promise<GameSnapshot>;
}
