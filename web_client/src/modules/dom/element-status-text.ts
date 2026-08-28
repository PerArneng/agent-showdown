import type { StatusText } from "../../interfaces/dom/index.js";

/** Edge module. */
export class ElementStatusText implements StatusText {
  constructor(private readonly element: HTMLElement) {}

  show(message: string): void {
    this.element.textContent = message;
  }
}
