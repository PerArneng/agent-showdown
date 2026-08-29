import type { Clock } from "../../src/interfaces/clock/index.js";

/** Test fake. Records sleeps instead of taking them, so a replay finishes instantly. */
export class FrozenClock implements Clock {
  readonly slept: number[] = [];

  async sleep(milliseconds: number): Promise<void> {
    this.slept.push(milliseconds);
  }

  /** Let every pending replay run to completion. Nothing here actually waits. */
  async settled(): Promise<void> {
    for (let turn = 0; turn < 1000; turn++) {
      await Promise.resolve();
    }
  }
}
