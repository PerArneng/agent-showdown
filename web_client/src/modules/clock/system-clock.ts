import type { Clock } from "../../interfaces/clock/index.js";

/** Edge module. The only code that calls `setTimeout`. */
export class SystemClock implements Clock {
  sleep(milliseconds: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
  }
}
