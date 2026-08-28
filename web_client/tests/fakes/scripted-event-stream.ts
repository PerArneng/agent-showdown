import type { EventStream, Subscription } from "../../src/interfaces/event_stream/index.js";
import type { GameEvent } from "../../src/interfaces/game/index.js";

/** Test fake. Hands over a canned list the moment anyone subscribes. */
export class ScriptedEventStream implements EventStream {
  closed = false;
  private emit: ((event: GameEvent) => void) | null = null;
  private changeConnection: ((connected: boolean) => void) | null = null;

  constructor(private readonly events: readonly GameEvent[] = []) {}

  subscribe(
    onEvent: (event: GameEvent) => void,
    onConnectionChange?: (connected: boolean) => void,
  ): Subscription {
    this.emit = onEvent;
    this.changeConnection = onConnectionChange ?? null;
    onConnectionChange?.(true);
    for (const event of this.events) {
      onEvent(event);
    }
    return {
      close: () => {
        this.closed = true;
        onConnectionChange?.(false);
      },
    };
  }

  /** Push one more event after subscribing, for tests about ordering. */
  push(event: GameEvent): void {
    this.emit?.(event);
  }

  /** Simulate connection state change, for tests about network events. */
  setConnected(connected: boolean): void {
    this.changeConnection?.(connected);
  }
}
