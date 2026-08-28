import type { StartButton } from "../../interfaces/dom/index.js";

/** Edge module. */
export class ElementStartButton implements StartButton {
  constructor(private readonly element: HTMLButtonElement) {}

  onClick(handler: () => void): void {
    this.element.addEventListener("click", handler);
  }

  setEnabled(enabled: boolean): void {
    this.element.disabled = !enabled;
  }
}
