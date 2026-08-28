import type { GameSnapshot } from "../../interfaces/game/index.js";
import type { GameApi } from "../../interfaces/game_api/index.js";

/** Edge module. The only code that calls `fetch`. */
export class HttpGameApi implements GameApi {
  constructor(
    private readonly startUrl: string,
    private readonly stateUrl: string,
  ) {}

  async startGame(): Promise<void> {
    await fetch(this.startUrl, { method: "POST" });
  }

  async fetchSnapshot(): Promise<GameSnapshot> {
    const response = await fetch(this.stateUrl);
    return (await response.json()) as GameSnapshot;
  }
}
