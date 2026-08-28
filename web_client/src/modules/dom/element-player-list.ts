import type { PlayerList } from "../../interfaces/dom/index.js";
import type { PlayerState } from "../../interfaces/game/index.js";

/** Edge module. Writes the roster into the document. */
export class ElementPlayerList implements PlayerList {
  constructor(
    private readonly element: HTMLElement,
    private readonly document: Document
  ) {}

  show(players: readonly PlayerState[]): void {
    this.element.replaceChildren(
      ...(players.length === 0 ? [this.empty()] : players.map((player) => this.row(player)))
    );
  }

  private empty(): HTMLElement {
    const item = this.document.createElement("li");
    item.className = "empty";
    item.textContent = "None yet";
    return item;
  }

  private row(player: PlayerState): HTMLElement {
    const item = this.document.createElement("li");
    const swatch = this.document.createElement("span");
    swatch.className = "swatch";
    swatch.style.background = player.color;
    const name = this.document.createElement("span");
    name.textContent = player.name;
    const cell = this.document.createElement("span");
    cell.className = "cell";
    cell.textContent = `${player.position.x},${player.position.y}`;
    item.append(swatch, name, cell);
    return item;
  }
}
