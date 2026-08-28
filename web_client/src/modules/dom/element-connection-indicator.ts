import type { ConnectionIndicator } from "../../interfaces/dom/index.js";

/** Edge module. Updates the connection indicator element in the DOM. */
export class ElementConnectionIndicator implements ConnectionIndicator {
  private readonly labelElement: HTMLElement | null;

  constructor(private readonly element: HTMLElement) {
    this.labelElement = element.querySelector<HTMLElement>(".connection-label");
  }

  show(connected: boolean): void {
    this.element.classList.toggle("connected", connected);
    this.element.classList.toggle("disconnected", !connected);
    const target = this.labelElement ?? this.element;
    target.textContent = connected ? "Connected" : "Disconnected";
  }
}
