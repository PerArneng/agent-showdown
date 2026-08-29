import type { GameSnapshot } from "../../interfaces/game/index.js";
import type { GameApi } from "../../interfaces/game_api/index.js";

const NOTHING_YET: GameSnapshot = {
  board: null,
  max_rounds: 0,
  round_number: 0,
  playing: false,
  paused: false,
  registered: [],
  players: [],
};

/** Demo mode. There is no server to ask; the fixture is already playing. */
export class OfflineGameApi implements GameApi {
  async newGame(): Promise<void> {}

  async fetchSnapshot(): Promise<GameSnapshot> {
    return NOTHING_YET;
  }
}
