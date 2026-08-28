import type { ConnectionIndicator } from "../../src/interfaces/dom/index.js";

/** Test fake. Keeps track of the last connection state shown. */
export class InMemoryConnectionIndicator implements ConnectionIndicator {
  readonly calls: boolean[] = [];

  show(connected: boolean): void {
    this.calls.push(connected);
  }

  last(): boolean | undefined {
    return this.calls.at(-1);
  }
}
