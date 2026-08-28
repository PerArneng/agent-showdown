import type { GameApi } from "../../interfaces/game_api/index.js";

/** Edge module. The only code that calls `fetch`. */
export class HttpGameApi implements GameApi {
  constructor(private readonly url: string) {}

  async startGame(): Promise<void> {
    await fetch(this.url, { method: "POST" });
  }
}
