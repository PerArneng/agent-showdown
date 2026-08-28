import type { PlayerList } from "../../src/interfaces/dom/index.js";
import type { PlayerState } from "../../src/interfaces/game/index.js";

/** Test fake. No document, no jsdom. */
export class InMemoryPlayerList implements PlayerList {
  shown: readonly PlayerState[] = [];

  show(players: readonly PlayerState[]): void {
    this.shown = players;
  }

  names(): readonly string[] {
    return this.shown.map((player) => player.name);
  }
}
