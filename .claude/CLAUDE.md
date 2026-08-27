# agent-showdown

Python CLI managed with **uv**. Run it as `uv run agent-showdown <subcommand>`.
Today there is one subcommand: `start`.

## Architecture

- A `Protocol` in front of every module. Depend on the Protocol, never on the class.
- `interfaces/` holds Protocols and frozen Pydantic models only — no behaviour, and it never imports
  from `modules/` or `cli/`. `modules/` holds the implementations under the same domain names.
- Domains today: `clock`, `console`, `file_system`, `randomizer`, `log`, `game`,
  `agent_client`, `engine`. Read the real contracts in `src/agent_showdown/interfaces/`.
- **One public class per file**, filename = class name in snake_case (`LocalFileSystem` →
  `local_file_system.py`).
- **IO only in the edge modules**: `modules/clock`, `modules/console`, `modules/file_system`,
  `modules/randomizer`. No `print()`, `open()`, `datetime.now()` or `random` anywhere else —
  randomness is nondeterministic input, so it is confined exactly like the clock.
- **Constructor injection only.** No globals, no module-level singletons, nothing constructing its
  own collaborators.
- `Engine` is the facade. Every use case is a method on it; frontends are thin adapters with zero
  logic, so a CLI and a web API are interchangeable.
- `mypy --strict` clean, and everything is testable in memory.
- Dependency direction, strictly one way: `cli → container → modules → interfaces`.

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
  listener added afterwards silently misses it. `Engine.start` relies on this ordering.
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
- **`Player` is synchronous and stays that way.** A2A's JSON-RPC `SendMessage` blocks by default, so
  a remote player needs no `async` — nothing forces it onto `Game`, `Engine` or the CLI.
- `modules/agent_client/` is intentionally empty. `A2APlayer` is a pure translator proven against a
  fake transport; the real HTTP client is not written yet. `A2APlayerFactory` uses the player name
  as the A2A `contextId` — a per-game unique id needs a `uuid`, which is nondeterministic input and
  would arrive as its own edge module.

## Gotchas

- **Typer**: an app with a single `@app.command()` collapses into a bare command, so
  `agent-showdown start` would fail with exit 2. `cli/main.py` keeps an `@app.callback()` to hold it
  as a command group. Redundant once a second subcommand exists; harmless to leave.
- **mypy**: `plugins = ["pydantic.mypy"]` is required, or `--strict` misses assignment to frozen
  model fields.

## Commands

```
uv sync                        # install
uv run agent-showdown start    # run
uv run pytest                  # test
uv run mypy src tests          # types
uv run ruff check src tests    # lint
```

Runtime deps: `typer`, `dependency-injector`, `pydantic`. Dev: `pytest`, `mypy`, `ruff`.
Python >= 3.11.

## Adding a feature

1. Add the `Protocol` in `interfaces/<domain>/<class_name>.py` — one public class per file.
2. Add new models as frozen Pydantic classes in the same `interfaces/<domain>/`.
3. Implement in `modules/<domain>/<impl_name>.py`, constructor-injected dependencies only.
4. Re-export from both sub-package `__init__.py` files.
5. Register it in `container.py`.
6. Expose the capability as a method on `Engine` — not in the CLI.
7. Add a thin Typer subcommand that only calls that method.
8. Unit-test the pure class in memory; add an engine integration test using the fakes.
9. Check no `print()`, `open()`, `datetime.now()` or `random` crept in outside the edge modules.
