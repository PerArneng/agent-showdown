# Antigravity Workspace Guidelines: agent-showdown

When working with Antigravity in this repository, the primary focus is on the **web client** located in `web_client/`. 

The `web_client` is a freestanding TypeScript project with its own toolchain, tests, and zero runtime dependencies, designed to render the `agent-showdown` board and stream game events from the backend server or demo fixtures. It adheres to the same hexagonal/clean architecture principles as the Python server, adapted for TypeScript and the browser environment.

---

## Architecture Rules (Adapted for TypeScript & `web_client/`)

### 1. Interface-First Design (`interfaces/` vs `modules/`)
- **Interface in front of every module**: Every domain module is governed by a contract. Code must depend strictly on TypeScript interfaces and types, never on concrete classes.
- **Pure `src/interfaces/`**: Holds TypeScript interfaces, type definitions, and readonly data contracts only.
  - Zero behavior, zero implementation code, and zero runtime overhead.
  - **Never imports from `src/modules/`, `container.ts`, or `main.ts`**.
- **Implementations in `src/modules/`**: Holds concrete class implementations grouped under domain subdirectories mirroring the interface structure.

### 2. Domain Boundaries
The client is partitioned into distinct domains:
- `game`: Core game state representation, immutable models (`ClientState`, `PlayerState`, `Board`, `Position`), `GameEvent` definitions, the pure `StateReducer`, and board rendering logic.
- `event_stream`: Contracts and adapters for streaming game events (`EventStream`, `SseEventStream`, `FixtureEventStream`).
- `game_api`: Contracts and adapters for game lifecycle triggers (`GameApi`, `HttpGameApi`, `OfflineGameApi`).
- `canvas`: Abstraction over 2D graphic surfaces (`Canvas`, `Html5Canvas`).
- `dom`: UI component abstractions for HTML elements (`PlayerList`, `StatusText`, `StartButton`).
- `clock`: Time abstraction for timestamps and delays (`Clock`, `SystemClock`).
- `engine`: Top-level facade orchestrating state, rendering, streams, and UI updates (`Engine`, `DefaultEngine`).

### 3. File & Class Organization
- **One public class / interface / type per file**: Every file exports a single primary contract or implementation.
- **Kebab-case file naming**: The filename matches the exported class or interface in kebab-case:
  - `Html5Canvas` → `html5-canvas.ts`
  - `DefaultStateReducer` → `default-state-reducer.ts`
  - `ClientState` → `client-state.ts`
  - `EventStream` → `event-stream.ts`

### 4. Strict IO & Non-Determinism Isolation in Edge Modules
- **Edge Modules**: Only the following modules are permitted to perform browser IO, touch DOM/Canvas APIs, use timers, or make network calls:
  - `modules/canvas` (interacts with `HTMLCanvasElement` & `CanvasRenderingContext2D`)
  - `modules/dom` (interacts with DOM `HTMLElement`, `Document`)
  - `modules/event_stream` (interacts with `EventSource` or fixture arrays)
  - `modules/game_api` (interacts with `fetch`)
  - `modules/clock` (interacts with `Date.now()` and `setTimeout`)
- **Forbidden outside Edge Modules**: No `document`, `window`, `fetch`, `EventSource`, `setTimeout`, `setInterval`, `requestAnimationFrame`, or `Math.random` anywhere else.
- Pure modules (such as `DefaultStateReducer`, `Palette`, `BoardRenderer`, `DefaultEngine`) are 100% deterministic, side-effect free, and unit-testable in memory.

### 5. Time & Clock Edge
- `Clock` owns the entire time boundary: both `now()` and `sleep()`.
- Any pure or asynchronous module that requires time delays (such as `FixtureEventStream` replaying turns) must receive an injected `Clock`.
- In tests, `FrozenClock` records sleeps and advances instantly, keeping tests fast and deterministic with no real-time waits.

### 6. Composition Root & Process Entry Point
- **Entry Point (`src/main.ts`)**:
  - Analogous to `cli/main.py` in the backend.
  - It is the single browser bootstrap: reads `window.location` (e.g. `?demo`), queries required DOM root elements (`#board`, `#players`, `#status`, `#start`), and passes them to `container.ts`.
  - Nothing below `main.ts` accesses globals, `window`, or queries DOM nodes.
- **Composition Root (`src/container.ts`)**:
  - The sole place where concrete classes are imported, instantiated, and wired together.
  - **Constructor injection only**: No singletons, no module-level global instances, and no classes constructing their own collaborators (`new Collaborator()` inside a class is forbidden).
  - Makes demo mode a clean configuration swap (`FixtureEventStream` + `OfflineGameApi` vs `SseEventStream` + `HttpGameApi`) rather than branching logic scattered through client code.

### 7. Facade Pattern (`Engine`)
- `Engine` is the facade for all client operations and use cases (`connect()`, `startGame()`).
- Frontends and UI event handlers are thin adapters that delegate to `Engine`.

### 8. Strict One-Way Dependency Direction
- Dependencies flow strictly in one direction:
  $$\text{main} \longrightarrow \text{container} \longrightarrow \text{modules} \longrightarrow \text{interfaces}$$
- Modules only depend on interfaces when collaborating across domain boundaries.

### 9. State Immutability & Frozen Model Rule
- State structures (`ClientState`, `PlayerState`, `Position`, `Board`) are deeply `readonly`.
- `DefaultStateReducer.reduce(state, event)` is a pure function that returns a **new** state object on every event (the frozen-model rule), eliminating mutable drift between the server and client.

### 10. Strict Typing & Pure In-Memory Testability
- `tsc --noEmit` must pass cleanly under `strict` mode with `verbatimModuleSyntax`.
- Tests run purely in-memory with Vitest: **no browser and no jsdom**. Canvas and DOM are behind interfaces, so tests use lightweight fakes (`RecordingCanvas`, `ScriptedEventStream`, `FrozenClock`).

---

## Conventions & Coding Standards

- **Naming Conventions**:
  - **No `I` prefix** on interfaces (use `Canvas`, `EventStream`, `GameApi`, `Clock`).
  - **Implementation prefixes**: Describe the mechanism or role: `Default…`, `Element…`, `Html5…`, `System…`, `Sse…`, `Fixture…`, `Http…`, `Offline…`.
  - **Test fake prefixes** in `tests/fakes/`: Describe behavior: `Recording…`, `Scripted…`, `Frozen…`, `InMemory…`.
- **Domain Import Boundary**:
  - When importing across domains, import through the domain's `index.ts`, not internal leaf files:
    ```typescript
    import type { GameEvent } from "../../interfaces/game/index.js";
    ```
- **TypeScript Import Rules**:
  - **Relative imports of modules must end in `.js`** (e.g. `import { Palette } from "./palette.js"`), required by `verbatimModuleSyntax`.
  - JSON files are imported with type assertions: `import data from "../fixtures/demo-game.json" with { type: "json" };`.
  - Use `import type` for type-only imports.
- **Zero Runtime Dependencies**:
  - Production code contains no external npm dependencies. Everything running in the browser is our own code. Only dev dependencies (`vite`, `typescript`, `vitest`, `prettier`, `vite-plugin-singlefile`) are permitted.

---

## Event Model & Backend Seam

- **Contract Synchronization**:
  - `src/interfaces/game/game-event.ts` mirrors the Python backend event models (`interfaces/game/*_event.py`), discriminated on the `type` field.
  - Adding a game event in the backend requires adding the corresponding type in TypeScript.
- **Exhaustive Reducer Switching**:
  - The `switch (event.type)` in `DefaultStateReducer` must remain exhaustive.
  - **Never add a `default:` branch** — this ensures `tsc` alerts you at build time if any event variant is unhandled.
- **No Runtime Validation (`zod`)**:
  - The backend is a strongly typed server emitting known event structures; client and server share contract definitions.

---

## Key Gotchas

1. **Load-Bearing Single-File Build**:
   - `vite-plugin-singlefile` inlines JS and CSS into `dist/index.html` with `base: "./"`.
   - Browsers reject ES module scripts and external stylesheets when opened via `file://` URLs. The single-file build ensures demo mode runs directly from disk without requiring a web server.
2. **Demo Mode Isolation**:
   - `?demo` swaps `SseEventStream` for `FixtureEventStream` and `HttpGameApi` for `OfflineGameApi` inside `container.ts`.
   - Downstream components have zero awareness of demo mode. An `if (demo)` check below `container.ts` is considered an architectural violation.
3. **Fixture Bundling**:
   - Fixtures are bundled via static JSON import rather than `fetch` (which fails on `file://`).
   - `FixtureEventStream` defers its first emitted event by a microtask to allow listeners to complete subscription before delivery.
4. **Backend-Frontend Seam**:
   - Python backend serves `web_client/dist` at `GET /`.
   - SSE connection: `GET /api/events` (idle keepalive via `: ping`).
   - Control API: `POST /api/start` (responds with HTTP 202 Accepted).

---

## Development Commands

### Web Client (`web_client/`)

```bash
# Install dependencies
npm --prefix web_client install

# Build single-file bundle to web_client/dist/ (required before backend can serve it)
npm --prefix web_client run build

# Watch mode during client development (rebuilds dist on change)
npm --prefix web_client run dev

# Run unit and integration tests (Vitest, in-memory)
npm --prefix web_client test

# Type check (strict mode)
npm --prefix web_client run check

# Code formatting (Prettier)
npm --prefix web_client run format
```

### Full-Stack / Backend Context (Root)

When running the Python server to serve the client:

```bash
# Sync Python environment
uv sync

# Start server on default port 8066 (serves web_client/dist)
uv run agent-showdown start

# Run backend tests / type checks / linting
uv run pytest
uv run mypy src tests
uv run ruff check src tests
```

---

## Adding a Feature to the Web Client

1. **Define Contract**: Add the interface or type in `src/interfaces/<domain>/<name>.ts` (one public contract per file).
2. **Implement**: Implement the interface in `src/modules/<domain>/<impl>.ts` (constructor injection only).
3. **Re-export**: Export from both domain `index.ts` files (`src/interfaces/<domain>/index.ts` and `src/modules/<domain>/index.ts`).
4. **Wire Dependencies**: Wire the new implementation in `src/container.ts`.
5. **Verify Purity**: Ensure no direct DOM/IO/timer/random calls exist outside edge modules.
6. **Test**: Write unit tests in `tests/unit/` using fakes, and extend `tests/integration/default-engine.test.ts` if engine wiring changed.
7. **Type Check & Format**: Run `npm --prefix web_client run check` and `npm --prefix web_client run format`.
