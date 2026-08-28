import type { EventStream, Subscription } from "../../interfaces/event_stream/index.js";
import type { GameEvent } from "../../interfaces/game/index.js";

/** Edge module. The live game, over Server-Sent Events. */
export class SseEventStream implements EventStream {
  constructor(private readonly url: string) {}

  subscribe(onEvent: (event: GameEvent) => void): Subscription {
    const source = new EventSource(this.url);
    source.onmessage = (message: MessageEvent<string>) => {
      onEvent(JSON.parse(message.data) as GameEvent);
    };
    return { close: () => source.close() };
  }
}
