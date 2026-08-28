import type { GameApi } from "../../interfaces/game_api/index.js";

/** Demo mode. There is no server to ask; the fixture is already playing. */
export class OfflineGameApi implements GameApi {
  async startGame(): Promise<void> {}
}
