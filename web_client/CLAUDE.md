# agent-showdown web client

The browser client for `agent-showdown`. A freestanding TypeScript project — its own toolchain, its
own tests, no runtime dependencies — built on the same architecture as the Python app one directory
up. `../.claude/CLAUDE.md` covers the server that serves this; everything below is about the client.

## Architecture

- An `interface` in front of every module. Depend on the interface, never on the class.
- `interfaces/` holds types only — no behaviour, and it never imports from `modules/`. `modules/`
  holds the implementations under the same domain names.
- Domains today: `game`, `event_stream`, `game_api`, `canvas`, `dom`, `clock`, `engine`. Read the
  real contracts in `src/interfaces/`.
- **One public class per file**, filename = class name in kebab-case (`Html5Canvas` →
  `html5-canvas.ts`).
- **IO only in the edge modules**: `modules/canvas`, `modules/dom`, `modules/event_stream`,
  `modules/game_api`, `modules/clock`. No `document`, `fetch`, `EventSource`, `setTimeout` or
  `Math.random` anywhere else. This is greppable, and worth grepping for.
- `main.ts` is the one exception, as `cli/main.py` is on the Python side: it reads
  `window.location` and `document.querySelector` to find the elements, then hands them to the
  container. Nothing below it touches a global.
- **Constructor injection only.** No globals, no module-level singletons, nothing constructing its
  own collaborators. `container.ts` is the sole composition root — the only place an implementation
  is named.
- `Engine` is the facade. `tsc --noEmit` clean under `strict`, and everything testable in memory.
- Dependency direction, strictly one way: `main → container → modules → interfaces`.

## Conventions

- No `I` prefix on interfaces. Implementations carry a qualifying prefix that says what kind they
  are: `Default…`, `Element…`, `Html5…`, `System…`, `Sse…`, `Fixture…`, `Http…`, `Offline…`. Fakes
  in `tests/fakes/` say what they do: `Recording…`, `Scripted…`, `Frozen…`, `InMemory…`.
- Import a domain through its `index.ts`, not a leaf file, when crossing domains:
  `import type { GameEvent } from "../../interfaces/game/index.js"`.
- **Relative imports of modules end in `.js`**, even from `.ts`: `verbatimModuleSyntax` is on and
  the emitted specifier is what the browser resolves. JSON is the exception — it is imported by its
  real name with `with { type: "json" }`. Use `import type` for types.
- No runtime dependencies. Nothing ships to the browser but our own code.

## State

`ClientState` is `readonly` throughout and `DefaultStateReducer` returns a **new** one every time —
this is the frozen-model rule, and it is what stops the screen drifting from what the server said.

`reduce(state, event) -> ClientState` is the whole client's logic, and it is pure: no DOM, no
canvas, no time, no randomness. Anything worth testing belongs there rather than in a view.

## Events

`src/interfaces/game/game-event.ts` mirrors `interfaces/game/*_event.py`, discriminated on `type`.

- Adding a listener method on the Python side means adding the variant here too. `tsc` will then
  point at the `switch` in `DefaultStateReducer` that no longer covers every case — the exhaustive
  switch is deliberate, so do not add a `default` branch to silence it.
- `tests/unit/demo-fixture.test.ts` reads the recorded fixture and catches drift between the two
  sides in the meantime.
- **No runtime validation, deliberately.** The only publisher is our own typed server; `zod` would
  be a runtime dependency for a boundary already checked at both ends. That changes only if the
  client ever consumes a stream it does not control.

## Testing

- The canvas and the DOM sit behind interfaces, so **the tests need no browser and no jsdom.**
  Never add one — needing it means an edge leaked into something that should be pure.
- Prefer fakes over mocks. `RecordingCanvas` asserts exact draw calls; `ScriptedEventStream` hands
  over a canned game; `FrozenClock` records sleeps instead of taking them.
- `tests/integration/default-engine.test.ts` runs a whole recorded game through the engine against
  fakes. That is the test that proves the wiring.

## Commands

```
npm install
npm run build    # -> dist/, which the Python server serves
npm run dev      # vite build --watch: edit, reload the browser, no server restart
npm test         # vitest, no browser
npm run check    # tsc --noEmit, strict
npm run format   # prettier
```

Dev dependencies only: `vite`, `typescript`, `vitest`, `prettier`.

## Gotchas

- **The build must stay single-file.** `vite-plugin-singlefile` inlines the JavaScript and CSS into
  `dist/index.html`, and `base: "./"` keeps what is left relative. Both are load-bearing: browsers
  refuse to load module scripts and stylesheets from a `file://` origin, so a multi-file build opens
  from disk as unstyled HTML with a blank canvas. Verified with a headless screenshot, not by
  reading the build output — the file names all looked right while the page was broken.
- **The fixture is imported, not fetched**, for the same reason: `fetch` is blocked on `file://`.
  Importing bundles it into the JavaScript, so `?demo` works with no server at all.
- **Demo mode is not a branch in the client.** `?demo` swaps `SseEventStream` for
  `FixtureEventStream` and `HttpGameApi` for `OfflineGameApi` in `container.ts`; nothing downstream
  knows it exists. Keep it that way — a `if (demo)` below the container is a bug.
- **`FixtureEventStream` defers its first event by a microtask on purpose.** A real stream never
  delivers from inside `subscribe`, and code downstream should not have to cope with one that does.

## Adding a feature

1. Add the `interface` in `src/interfaces/<domain>/<name>.ts` — one public thing per file.
2. Implement it in `src/modules/<domain>/<impl>.ts`, constructor-injected dependencies only.
3. Re-export from both `index.ts` files.
4. Wire it in `container.ts` — not in `main.ts`, and not by importing it where it is used.
5. Unit-test the pure class against fakes; extend the engine integration test if the wiring changed.
6. Check no `document`, `fetch`, `EventSource`, `setTimeout` or `Math.random` crept in outside the
   edge modules.
