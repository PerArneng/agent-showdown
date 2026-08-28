import type { Clock } from "../../interfaces/clock/index.js";
import type { EventStream, Subscription } from "../../interfaces/event_stream/index.js";
import type { GameEvent } from "../../interfaces/game/index.js";

/**
 * A recorded game, replayed on the clock. No network, no server, no Python.
 *
 * It is an `EventStream` like any other, which is the whole trick: nothing downstream can tell it
 * from the live one.
 */
export class FixtureEventStream implements EventStream {
  constructor(
    private readonly events: readonly GameEvent[],
    private readonly clock: Clock,
    private readonly delayMilliseconds: number
  ) {}

  subscribe(onEvent: (event: GameEvent) => void): Subscription {
    let open = true;
    // Start after the caller has its subscription back. A real stream never delivers an event
    // from inside `subscribe`, and code downstream should not have to cope with one that does.
    void Promise.resolve().then(() => this.replay(onEvent, () => open));
    return { close: () => void (open = false) };
  }

  private async replay(
    onEvent: (event: GameEvent) => void,
    isOpen: () => boolean
  ): Promise<void> {
    for (const event of this.events) {
      if (!isOpen()) {
        return;
      }
      onEvent(event);
      await this.clock.sleep(this.delayMilliseconds);
    }
  }
}
