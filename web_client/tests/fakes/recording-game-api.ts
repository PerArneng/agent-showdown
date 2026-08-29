import type { GameSnapshot } from "../../src/interfaces/game/index.js";
import type { GameApi } from "../../src/interfaces/game_api/index.js";

const NOTHING_YET: GameSnapshot = {
  board: null,
  max_rounds: 0,
  round_number: 0,
  playing: false,
  paused: false,
  registered: [],
  players: [],
};

/** Test fake. Counts the games it was asked to start, and hands back a canned snapshot. */
export class RecordingGameApi implements GameApi {
  started = 0;
  snapshots = 0;

  constructor(private readonly snapshot: GameSnapshot = NOTHING_YET) {}

  async newGame(): Promise<void> {
    this.started++;
  }

  async fetchSnapshot(): Promise<GameSnapshot> {
    this.snapshots++;
    return this.snapshot;
  }
}
