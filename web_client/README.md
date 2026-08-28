# agent-showdown web client

The board you watch the game on. A freestanding TypeScript project: its own toolchain, its own
tests, and a demo mode that runs with no Python at all.

## Commands

```bash
npm install
npm run build     # -> dist/, which the Python server serves
npm run dev       # rebuild on every change; reload the browser
npm test          # vitest, no browser involved
npm run check     # tsc --noEmit, strict
```

## Two ways to run it

**Against the server.** Build once, then `uv run agent-showdown start` from the repo root and open
<http://127.0.0.1:8066>. The server prefers `web_client/dist` over its packaged copy, so
`npm run dev` in one terminal and a browser reload is the whole loop — no restart.

**With no server at all.** Open `dist/index.html?demo` straight from disk. A recorded game replays
from `fixtures/demo-game.json`, which is bundled into the JavaScript rather than fetched, because
`fetch` is blocked on `file://`.

Demo mode is not a special case in the client. It is a different `EventStream` implementation,
chosen in `container.ts` and invisible to everything downstream:

| | live | `?demo` |
|---|---|---|
| `EventStream` | `SseEventStream` | `FixtureEventStream` |
| `GameApi` | `HttpGameApi` | `OfflineGameApi` |

## How it is built

The same architecture as the Python side, translated:

- **An interface in front of every module.** `interfaces/` holds types only — no behaviour, and it
  never imports from `modules/`. Implementations mirror it under the same domain names.
- **IO only in the edge modules.** Nothing outside `modules/canvas`, `modules/dom`,
  `modules/event_stream`, `modules/game_api` and `modules/clock` may touch `document`, `fetch`,
  `EventSource`, `setTimeout` or `Math.random`. This is greppable, and worth grepping for.
- **Constructor injection only.** No globals, no singletons, nothing building its own collaborators.
  `container.ts` is the only place an implementation is named.
- **One public class per file**, filename = class name in kebab-case.
- **State is a value.** `ClientState` is `readonly` throughout and `DefaultStateReducer` returns a
  new one every time, so nothing on screen can drift from what the server said.
- `tsc --noEmit` clean under `strict`.

The payoff is `npm test`: the canvas and the DOM are interfaces, so the entire client — a whole
recorded game, end to end — is tested with no browser and no jsdom.

## Layout

```
src/
  main.ts        composition root: finds the elements, picks live or demo
  container.ts   builds the object graph
  interfaces/    game, event_stream, game_api, canvas, dom, clock, engine
  modules/       the implementations, same domain names
tests/
  fakes/         RecordingCanvas, ScriptedEventStream, FrozenClock, InMemory* views
  unit/          per class, pure
  integration/   the whole engine against fakes
fixtures/        a recorded game, used by demo mode and by the tests
```

## Adding an event

The event types in `src/interfaces/game/game-event.ts` mirror `interfaces/game/*_event.py` on the
Python side, discriminated on `type`. Add the case there and `tsc` will point at the `switch` in
`DefaultStateReducer` that no longer covers every variant. Generating the union from the server's
JSON schema is the obvious follow-up; `tests/unit/demo-fixture.test.ts` catches drift in the
meantime.

There is **no runtime validation**, deliberately: the only publisher is our own typed server, and
`zod` would be a runtime dependency for a boundary that is checked at both ends. That changes if the
client ever consumes a stream it does not control.
