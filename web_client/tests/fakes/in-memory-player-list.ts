import type { PlayerList } from "../../src/interfaces/dom/index.js";
import type { PlayerState } from "../../src/interfaces/game/index.js";

/** Test fake. No document, no jsdom. */
export class InMemoryPlayerList implements PlayerList {
  shown: readonly PlayerState[] = [];
  thinking: string | null = null;

  show(players: readonly PlayerState[], thinking: string | null = null): void {
    this.shown = players;
    this.thinking = thinking;
  }

  names(): readonly string[] {
    return this.shown.map((player) => player.name);
  }
}
