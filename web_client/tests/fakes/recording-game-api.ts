import type { GameApi } from "../../src/interfaces/game_api/index.js";

/** Test fake. Counts the games it was asked to start. */
export class RecordingGameApi implements GameApi {
  started = 0;

  async startGame(): Promise<void> {
    this.started++;
  }
}
