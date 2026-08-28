# agent-showdown

Python app managed with **uv**. `uv run agent-showdown start` serves the web client on
`--port` (default 8066); games are started from the browser. The client is a separate
TypeScript project in `web_client/` and **must be built first** — it has its own `CLAUDE.md`.

## Architecture

- A `Protocol` in front of every module. Depend on the Protocol, never on the class.
- `interfaces/` holds Protocols and frozen Pydantic models only — no behaviour, and it never imports
  from `modules/` or `cli/`. `modules/` holds the implementations under the same domain names.
- Domains today: `clock`, `console`, `file_system`, `randomizer`, `event_channel`, `log`,
  `game`, `agent_client`, `builtin_agents`, `config`, `engine`. Read the real contracts in
  `src/agent_showdown/interfaces/`.
- Two frontends, both thin adapters over `Engine`: `cli/` and `web/`. `cli/` builds the
  container and hands the pieces to `web.create_app`; nothing else may import `Container`.
  `web_client/` is a third, in TypeScript, over the HTTP the `web/` frontend exposes. It is a
  separate project governed by `web_client/CLAUDE.md`.
- **One public class per file**, filename = class name in snake_case (`LocalFileSystem` →
  `local_file_system.py`).
- **IO only in the edge modules**: `modules/clock`, `modules/console`, `modules/file_system`,
  `modules/randomizer`, `modules/event_channel`. No `print()`, `open()`, `datetime.now()`,
  `time.sleep()` or `random` anywhere else — randomness is nondeterministic input, so it is
  confined exactly like the clock.
- `Clock` owns the whole time edge: `now()` **and** `sleep()`. A pure class that wants to pause
  asks the clock, so `FrozenClock` can record the pause and return instantly.
- `event_channel` is an edge module for a different reason: it is where the thread playing the
  game meets the threads serving HTTP, so it owns the queues and the blocking waits. Concurrency
  lives in three places and nowhere else: here, in `web/`, and the one lock in `DefaultEngine`
  that keeps two games from running at once.
- **Constructor injection only.** No globals, no module-level singletons, nothing constructing its
  own collaborators.
- `Engine` is the facade. Every use case is a method on it; frontends are thin adapters with zero
  logic, so a CLI and a web API are interchangeable.
- `mypy --strict` clean, and everything is testable in memory.
- Dependency direction, strictly one way:
  `cli → web → container → modules → interfaces`. `cli/` is the process entry point and the
  composition root; `web/` receives what it needs and never reaches for the container.

## Conventions

- No `I` prefix on interfaces. Implementations carry a qualifying prefix: `Local…`, `System…`,
  `Stdio…`, `Ansi…`, `Default…`. Fakes in `tests/fakes/` say what they do:
  `InMemory…`, `Frozen…`, `Fixed…`, `Recording…`, `Scripted…`.
- Import from a sub-package, never from the leaf file:
  `from agent_showdown.interfaces.file_system import FileInfo, FileSystem`.
- Models are `BaseModel` with `model_config = ConfigDict(frozen=True)`: data only, no behaviour.
- One deliberate exception to "interfaces holds Protocols and frozen models only":
  `AgentClientError` lives in `interfaces/agent_client/`. Callers must handle it, so it is part
  of the contract, and putting it beside the implementation would force `modules/game` to
  import `modules/agent_client` and break the one-way `modules → interfaces` direction.
- Prefer stdlib types (`pathlib.Path`, `datetime`) over custom wrappers.
- `cli/main.py` is the sole composition root — the only place `Container()` is instantiated. Tests
  construct classes directly with fakes, or use `container.<provider>.override(...)`.

## Log output

Format is `{timestamp} {level} {message}`:

```
2025-09-10 INFO started
```

- `TIMESTAMP_FORMAT` is a single constant in `modules/log/ansi_log_formatter.py`.
- **Only the level token is colored** — never the timestamp, never the message. Raw ANSI from the
  pure formatter, no `rich`/`colorama`:

  | Level | Code |
  |---|---|
  | DEBUG | `\x1b[36m` |
  | INFO | `\x1b[32m` |
  | WARNING | `\x1b[33m` |
  | ERROR | `\x1b[31m` |
  | CRITICAL | `\x1b[1;31m` |
  | reset | `\x1b[0m` |

- The color is chosen inside the pure formatter, so tests assert exact escape sequences with no
  terminal involved. Any future `NO_COLOR`/TTY handling arrives as an injected flag — never sniff the
  terminal from a pure class.
- The package is `log`, not `logging`, so it never reads as the stdlib module.

## The game

`Game` owns the rules, `Player` implementations are the contestants, `GameListener` observes. A
player never sees the board — only its own `GameView`, handed to it once per turn.

- **Register listeners before players.** `register_player` emits `player_joined` immediately, so a
  listener added afterwards silently misses it. `Engine.start_game` relies on this ordering,
  which is also why the browser sees `player_joined` before `game_started`.
- **`take_turn` is a trust boundary.** A `Player` may be a remote agent, so `DefaultGame` wraps the
  call in a broad `except Exception` — deliberate, not sloppy — and reports it as `turn_failed`
  instead of letting one contestant kill the game.
- **`_MAX_MOVES_PER_TURN` caps a plan and rejects an over-long one *whole***, so nobody is given a
  partial turn they did not ask for. The value is arbitrary; revisit it once real agents show what
  plans actually look like.
- **Players are keyed by object, not name** (`dict[Player, Position]`) — two contestants may share
  a name.
- `Direction` is a bare `StrEnum`. The deltas live in `DefaultGame`, because which way is "up" is a
  rule of the board, not a property of the word. Do not add a `delta` property to the enum.
- Every event carries a `Position`, never loose `x`/`y` pairs.
- `turn_failed` logs at WARNING. Every other game event logs at INFO.
- **`PlayerTurn` carries a `reasoning` alongside the plan**, and `DefaultGame` reports it as
  `player_reasoned` *before* it judges the plan — so an over-long plan still says what it was for.
  An empty reasoning emits nothing, which is why a plain `ScriptedPlayer` leaves the event
  sequence untouched. The event reaches the browser like any other and lands in the player list.
- **`Player` is synchronous and stays that way.** A2A's JSON-RPC `SendMessage` blocks by default, so
  a remote player needs no `async` — nothing forces it onto `Game`, `Engine` or the CLI. The web
  frontend is the only async code, and it keeps the blocking game on a worker thread.
- **`Engine.start_game` plays a game; `cli start` serves the UI.** Running a match is a use case on
  the facade; serving is a frontend job. `start_game` refuses to run two games at once — two would
  interleave their events into one stream of listeners.
- **Every listener method has a matching frozen event model** in `interfaces/game/`, told apart by a
  `Literal` `type` and collected in the `GameEvent` union. `ChannelGameListener` is the only
  translator between the two. Adding a listener method means adding its event as well, and events
  name a player with a **string** — the wire needs something serializable.
- `modules/agent_client/` is intentionally empty. `A2APlayer` is a pure translator proven against a
  fake transport; the real HTTP client is not written yet. `A2APlayerFactory` uses the player name
  as the A2A `contextId` — a per-game unique id needs a `uuid`, which is nondeterministic input and
  would arrive as its own edge module.

## Built-in agents

`modules/builtin_agents/` holds contestants that live **in this process**. Nothing is served and
nothing is dialled over A2A — the container hands them to the engine like any other collaborator.
One sub-package per agent, named after it: `simple_strands/` today.

- **The player is pure, the model call is not.** `SimpleStrandsPlayer` renders a `GameView` into a
  prompt and hands it to a `TurnPlanner`. `StrandsTurnPlanner` is the only thing that imports
  `strands` or opens a socket, which is what keeps the player unit-testable in memory and the
  suite free of npm-style network flakiness. **No test may reach a real model**: override
  `container.agent_roster` with `ScriptedAgentRoster`, or the suite hangs on a DNS lookup.
- **`AgentRoster` is the unit the engine sees, not a `PlayerFactory`.** `SimpleStrandsRoster` takes
  a list of `AgentConfig`s and builds one `StrandsTurnPlanner` and one player per entry, so the
  same code plays several models at once — a vLLM box and a local LM Studio side by side. Each
  contestant names itself from its own config, which is why the roster replaced
  `SimpleStrandsPlayerFactory`: a factory that is handed a name cannot carry per-agent config.
- Constructing a `StrandsTurnPlanner` builds an `OpenAIModel` and opens no socket, so a roster may
  be constructed in a unit test as long as `plan()` is never called.
- A planner failure raises `AgentClientError` — the same contract a remote agent already uses, and
  `DefaultGame`'s trust boundary turns it into `turn_failed` either way. One unreachable endpoint
  therefore costs its own contestant its turns and leaves the rest of the game running.
- **A fresh `Agent` per turn.** The contestant is stateless by design, and an unchanging system
  prompt is what a vLLM prefix cache keys on. Reasoning tokens are spent out of `max_tokens`
  before any answer arrives, so budget it generously and set a timeout in the hundreds of seconds.
- `max_moves` on the config is what the *prompt* asks for; `_MAX_MOVES_PER_TURN` in `DefaultGame`
  is what the *rules* allow. Set the first below the second, or every turn is refused whole.
- **`thinking: false` is worth minutes per turn**, and it is *two* wire fields, not one:
  `_NO_THINKING` in `StrandsTurnPlanner` sends both `reasoning_effort: "none"` and
  `extra_body.chat_template_kwargs.enable_thinking: false`. Measured against both boxes:
  vLLM honours the chat-template switch and ignores `reasoning_effort`; LM Studio does exactly
  the reverse and also ignores a `/no_think` suffix. Each silently ignores the other's field,
  which is what lets one config flag work on either. Do not "simplify" this to one field
  without re-measuring against both servers.
- `params` on `OpenAIModel` is spread straight into `client.chat.completions.create(**request)`
  by strands, so `extra_body` reaches the server as top-level JSON. That is the seam for any
  future server-specific knob.
- `_AGENT_SEATS` in `DefaultEngine` is where the agents sit down, cycled — more agents than seats
  still starts a game, they just share corners.

## Configuration

`interfaces/config/` holds `AgentConfig` (name plus one OpenAI-compatible endpoint and its
budgets) and `AppConfig` (`agents: tuple[AgentConfig, ...]`). `YamlConfigLoader` reads them from
`agent-showdown.yaml`.

- **The defaults are in the models, so no file is needed.** A missing default path yields
  `AppConfig()` and the run still fields both built-in agents. A path named explicitly with
  `--config` that does not exist is an error instead — a wrong flag must not look like success.
- Both models are `extra="forbid"`, unlike every other frozen model here. They are filled from a
  hand-written file, so a typo'd key must fail loudly rather than leave a default in place.
- **Reading goes through the `file_system` edge module**, and `yaml.safe_load` runs on the string
  it returns — the no-`open()` rule holds and `InMemoryFileSystem` covers the loader in tests.
- **`container.config` is a `providers.Dependency`, resolved in two steps by the composition
  root**: loading the config needs `file_system`, which only exists once the container is built.
  So `cli/main.py` does `container.config.override(container.config_loader().load(config))`.
  `Dependency.override` wraps a plain value itself, which is why `cli/` still never imports
  `providers`. Any test that builds a `Container` must override `config` too, or `agent_roster`
  cannot resolve.

## Serving the web client

The client is a **separate project** in `web_client/`, with its own toolchain and its own
`CLAUDE.md` — read that before touching anything under it. This section is only the seam: how the
Python side finds and serves what that project builds.

- **It must be built before the server can serve it.** `find_client_dir` prefers `web_client/dist`
  over the packaged copy, so `npm run dev` plus a browser reload is the whole loop with no restart.
  `--client-dir` overrides the search and is validated the same way, so a wrong path fails like an
  unbuilt one.
- **The Python test suite must never need npm.** `InMemoryFileSystem` supplies a fake `dist/`.
- **The client builds to a single self-contained `index.html`**, so `GET /` is the only route that
  serves it — there is no static-asset handling to get wrong. That is not a packaging preference:
  browsers refuse to load module scripts from a `file://` origin, so a multi-file build cannot be
  opened from disk, and demo mode depends on exactly that.
- Served through the `file_system` edge module, not `StaticFiles`, so the no-`open()` rule holds.
  It is read per request, which is why `npm run dev` needs no server restart.
- **Server-Sent Events, not WebSockets.** Traffic is one-way; `POST /api/start` is the only thing
  the browser sends.
- **`GET /api/state` is the stream's missing half.** The event stream has no replay, so a browser
  that connects mid-game — or reloads during one — never hears `game_started` and has no board to
  draw. `SnapshotGameListener` keeps the game as a `GameSnapshot`, the engine hands it out through
  `SnapshotSource`, and the client folds it in with `reduce.catchUp`. It is a *listener*, so it
  stays in step with the stream for free: adding a `GameListener` method means deciding what it
  does to the snapshot too.
- **The snapshot has no lock, deliberately.** The game thread writes and HTTP threads read, but
  every write replaces the frozen snapshot rather than mutating it, and rebinding one attribute is
  atomic — a reader sees the old value or the new one, never a half-built board. Mutating it in
  place would need a lock and would break the rule that concurrency lives in three places.
- **The client subscribes before it fetches.** Otherwise an event arriving during the fetch is
  lost. `catchUp` therefore fills gaps only: the live stream is fresher and always wins.
- `GET /api/events` is endless by design — one connection outlives many games. It polls the
  channel with a timeout and emits `: ping` when idle, which is also how it notices the reader
  is gone. Do not try to read it with `TestClient`; drive `stream_events` directly instead.
- **The stream must watch `stopping()`**, or Ctrl-C hangs: uvicorn's graceful shutdown waits for
  open connections, and an endless stream never closes one. `WebServer.stopping` exposes uvicorn's
  own `should_exit` so the stream ends itself and the server exits without cancelling anything.
  The graceful-shutdown timeout is only a backstop.
- `POST /api/start` answers **202 before the game runs**, so a refused concurrent start still
  answers 202. The refusal shows up as a log line, not a status code.
- **Events must stay in step across the two projects.** A new `GameListener` method needs its
  Python event model *and* the matching variant in `web_client/src/interfaces/game/game-event.ts`.
  `GameSnapshot` mirrors the same way, in `web_client/src/interfaces/game/game-snapshot.ts`.

## Gotchas

- **Typer**: an app with a single `@app.command()` collapses into a bare command, so
  `agent-showdown start` would fail with exit 2. `cli/main.py` keeps an `@app.callback()` to hold it
  as a command group. Redundant once a second subcommand exists; harmless to leave.
- **mypy**: `plugins = ["pydantic.mypy"]` is required, or `--strict` misses assignment to frozen
  model fields.
- **`DummyPlayer` sleeps 500ms per turn** so a human can watch it move. Tests pass a
  `FrozenClock` and `think_time=0.0`, so the suite stays instant — never let a real clock into
  a test that plays a game.

## Commands

```
uv sync                        # install
uv run pytest                  # test
uv run mypy src tests          # types
uv run ruff check src tests    # lint
uv run agent-showdown start    # serve on 8066 (--port, --client-dir, --config)
```

The client is built separately, and the server has nothing to serve until it is:

```
npm --prefix web_client install
npm --prefix web_client run build   # required before `start` works
npm --prefix web_client run dev     # rebuild on save while working on the client
npm --prefix web_client test        # vitest, no browser
npm --prefix web_client run check   # tsc --noEmit
```

Runtime deps: `typer`, `dependency-injector`, `pydantic`, `pyyaml`, `fastapi`, `uvicorn`,
`strands-agents[openai]`.
Dev: `pytest`, `mypy`, `ruff`, `httpx`, `types-PyYAML`.
Python >= 3.11. The client's dependencies are all dev-only and live in `web_client/`.

Packaging: `web_client/dist` is force-included into the wheel as `agent_showdown/web/static`,
and named in `[tool.hatch.build] artifacts` as well — it is gitignored, so without that the
sdist drops it and `uv build` fails on the forced include.

## Adding a feature

1. Add the `Protocol` in `interfaces/<domain>/<class_name>.py` — one public class per file.
2. Add new models as frozen Pydantic classes in the same `interfaces/<domain>/`.
3. Implement in `modules/<domain>/<impl_name>.py`, constructor-injected dependencies only.
4. Re-export from both sub-package `__init__.py` files.
5. Register it in `container.py`.
6. Expose the capability as a method on `Engine` — not in the CLI.
7. Surface it in a frontend that only calls that method: a Typer subcommand, a route in
   `web/app.py`, or both.
8. Unit-test the pure class in memory; add an engine integration test using the fakes.
9. Check no `print()`, `open()`, `datetime.now()` or `random` crept in outside the edge modules.
