import type { StartButton } from "../../src/interfaces/dom/index.js";

/** Test fake. Lets a test click the button without a browser. */
export class InMemoryStartButton implements StartButton {
  enabled = true;
  private handler: (() => void) | null = null;

  onClick(handler: () => void): void {
    this.handler = handler;
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  click(): void {
    this.handler?.();
  }
}
