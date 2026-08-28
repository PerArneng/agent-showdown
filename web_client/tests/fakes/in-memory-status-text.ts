import type { StatusText } from "../../src/interfaces/dom/index.js";

/** Test fake. Keeps every line it was asked to show. */
export class InMemoryStatusText implements StatusText {
  readonly messages: string[] = [];

  show(message: string): void {
    this.messages.push(message);
  }

  last(): string | undefined {
    return this.messages.at(-1);
  }
}
