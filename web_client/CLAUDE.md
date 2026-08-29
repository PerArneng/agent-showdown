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

## Catching up

`GET /api/events` has no replay, so a client that connects mid-game — or reloads during one —
never hears `game_started` and has nothing to draw. `GameApi.fetchSnapshot()` fetches
`/api/state` and `reduce.catchUp(state, snapshot)` folds it in.

- **Subscribe first, then fetch.** `DefaultEngine.connect` opens the stream before asking for the
  snapshot, so no event can slip past while the request is in flight.
- **`catchUp` fills gaps only.** The snapshot was taken before it was asked for, so anything the
  live stream already delivered is fresher and wins — the board is kept if set, and a player the
  events introduced is never replaced. That is what makes the ordering above safe.
- It is on `StateReducer` rather than in the engine because it is state folding, and belongs where
  everything else worth testing lives.

## Events

`src/interfaces/game/game-event.ts` mirrors `interfaces/game/*_event.py`, discriminated on `type`.

- `game-snapshot.ts` mirrors `interfaces/game/game_snapshot.py` the same way, and drifts the
  same way if only one side is changed.
- Adding a listener method on the Python side means adding the variant here too. `tsc` will then
  point at the `switch` in `DefaultStateReducer` that no longer covers every case — the exhaustive
  switch is deliberate, so do not add a `default` branch to silence it.
- The fixture is a **recording of the real engine**, not hand-written. Re-record it rather than
  editing it by hand when the event shapes change.
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

- **Terrain arrives inside `Board`**, so `reduce` needed no new case and `catchUp` no new field —
  but `ThreeBoardRenderer`'s rebuild guard compared width and height only, and every match is the
  same size, so the layout is part of that comparison now. `board.obstacles` is optional because
  `fixtures/demo-game.json` was recorded before terrain existed; read it as `?? []`.
- **The obstacles have a `THREE.Group` of their own, and it is not an optimisation.** The arena is
  re-dealt every round, so `placeObstacles` runs far more often than the diorama beneath it.
  Ground, grid lines and the eight border trees rebuild only when the board's *size* changes;
  obstacles rebuild whenever the layout signature does. Rebuilding both together would tear down
  and re-raise the whole diorama at every round boundary, which flickers for nothing. `borderTrees`
  and `obstacles` are separate lists for the same reason; the occlusion fade walks both.
- **`createObstacleMesh` in `modules/game/obstacle-meshes.ts` picks the model for a square.**
  Every kind is a `.glb` now. Which variant, and how it is turned, comes from a deterministic
  hash of the square it stands on, because `Math.random` is an edge concern and this is not an
  edge module.
- **Measure a `.glb` through its node hierarchy, never from the accessor `min`/`max` alone.**
  These models are dozens of separately-placed stones, so the union of the mesh-local boxes is
  meaningless: it made every wall look a third of its true size and made the junction pieces look
  like identical symmetric crosses. Walking the nodes gives the truth — the wall models are
  authored *to the tile*, every arm reaching exactly 0.5 from the centre, so `WALL_SCALE` is 1.0
  and a piece meets its neighbour flush.
- **The wall models' native arms are not what you would guess**, so they are written down here:
  `stone-wall-middle` runs **east-west**, `stone-wall-2way` is an L with arms **west and south**,
  `stone-wall-3way` is a T with arms **east, west and south** (open to the north), `stone-wall-4way`
  is symmetric, and `stone-wall-end` reaches no edge at all — it is a lump for a lone square, not
  a cap. `tests/unit/obstacle-meshes.test.ts` asserts the model *and* the rotation for every
  neighbour pattern; asserting rotation alone is what let a wrong model choice go unnoticed, which
  is also why `ModelLoader.instantiate` stamps `userData.modelKey`.

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
