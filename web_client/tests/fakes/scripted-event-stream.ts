import type { EventStream, Subscription } from "../../src/interfaces/event_stream/index.js";
import type { GameEvent } from "../../src/interfaces/game/index.js";

/** Test fake. Hands over a canned list the moment anyone subscribes. */
export class ScriptedEventStream implements EventStream {
  closed = false;
  private emit: ((event: GameEvent) => void) | null = null;

  constructor(private readonly events: readonly GameEvent[] = []) {}

  subscribe(onEvent: (event: GameEvent) => void): Subscription {
    this.emit = onEvent;
    for (const event of this.events) {
      onEvent(event);
    }
    return { close: () => void (this.closed = true) };
  }

  /** Push one more event after subscribing, for tests about ordering. */
  push(event: GameEvent): void {
    this.emit?.(event);
  }
}
