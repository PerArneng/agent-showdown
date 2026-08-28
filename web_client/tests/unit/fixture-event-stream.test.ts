import { describe, expect, it } from "vitest";
import type { GameEvent } from "../../src/interfaces/game/index.js";
import { FixtureEventStream } from "../../src/modules/event_stream/index.js";
import { FrozenClock } from "../fakes/index.js";

const EVENTS: readonly GameEvent[] = [
  { type: "round_started", round_number: 1 },
  { type: "game_ended", rounds_played: 1 },
];

describe("FixtureEventStream", () => {
  it("replays every event, in order", async () => {
    const clock = new FrozenClock();
    const seen: GameEvent[] = [];

    new FixtureEventStream(EVENTS, clock, 250).subscribe((event) => seen.push(event));
    await clock.settled();

    expect(seen).toEqual(EVENTS);
  });

  it("waits the configured step between events", async () => {
    const clock = new FrozenClock();

    new FixtureEventStream(EVENTS, clock, 250).subscribe(() => {});
    await clock.settled();

    expect(clock.slept).toEqual([250, 250]);
  });

  it("stops replaying once the subscription is closed", async () => {
    const clock = new FrozenClock();
    const seen: GameEvent[] = [];

    const subscription = new FixtureEventStream(EVENTS, clock, 250).subscribe((event) => {
      seen.push(event);
      subscription.close();
    });
    await clock.settled();

    expect(seen).toHaveLength(1);
  });
});
