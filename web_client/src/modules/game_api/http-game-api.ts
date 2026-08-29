import type { GameSnapshot } from "../../interfaces/game/index.js";
import type { GameApi } from "../../interfaces/game_api/index.js";

/** Edge module. The only code that calls `fetch`. */
export class HttpGameApi implements GameApi {
  constructor(
    private readonly newGameUrl: string,
    private readonly stateUrl: string,
  ) {}

  async newGame(): Promise<void> {
    await fetch(this.newGameUrl, { method: "POST" });
  }

  async fetchSnapshot(): Promise<GameSnapshot> {
    const response = await fetch(this.stateUrl);
    return (await response.json()) as GameSnapshot;
  }
}
