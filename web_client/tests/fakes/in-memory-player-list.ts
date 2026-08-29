import type { PlayerList } from "../../src/interfaces/dom/index.js";
import type { PlayerState } from "../../src/interfaces/game/index.js";

/** Test fake. No document, no jsdom. */
export class InMemoryPlayerList implements PlayerList {
  shown: readonly PlayerState[] = [];
  thinking: string | null = null;
  registered: readonly string[] = [];
  paused = false;

  show(
    players: readonly PlayerState[],
    thinking: string | null = null,
    registered: readonly string[] = [],
    paused = false,
  ): void {
    this.shown = players;
    this.thinking = thinking;
    this.registered = registered;
    this.paused = paused;
  }

  names(): readonly string[] {
    return this.shown.map((player) => player.name);
  }
}
