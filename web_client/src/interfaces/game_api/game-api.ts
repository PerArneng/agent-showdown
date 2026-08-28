/** Asking the server to play a game. Edge: the live implementation posts over HTTP. */
export interface GameApi {
  startGame(): Promise<void>;
}
