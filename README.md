# agent-showdown

A turn-based game where the contestants are agents.

Players live on a 2D board. Each round the game asks every player for a turn, and a turn is a
*plan*: a sequential list of moves, each one a direction (the four orthogonals plus the four
diagonals). The game applies the plan, keeps everyone inside the board, and announces what happened
to anyone listening.

Today the board is an empty grid and the built-in players wander at random. The point is not the
game yet — it is the seam. A `Player` is a `Protocol` with two methods, so a remote agent speaking
the [A2A protocol](https://a2a-protocol.org/latest/specification/) can be a contestant beside a
local one, and the game cannot tell the difference.

## Running it

```bash
uv sync
uv run agent-showdown start          # http://127.0.0.1:8066, or --port
```

Open the page and press **Start game**. Two players appear in the sidebar with their own colors and
step around a 10x10 grid, half a second at a time so the movement is watchable. The same game still
logs to the terminal you started the server from:

```
2026-08-27 INFO serving on http://127.0.0.1:8066
2026-08-27 INFO started
2026-08-27 INFO player dummy-1 joined at (0,0)
2026-08-27 INFO player dummy-2 joined at (9,9)
2026-08-27 INFO game started on a 10x10 board for 10 rounds
2026-08-27 INFO round 1 started
2026-08-27 INFO player dummy-1 blocked moving LEFT from (0,0)
2026-08-27 INFO player dummy-2 moved from (9,9) to (8,9)
```

The browser sees the same events, because the terminal log and the browser are two `GameListener`s
watching one game. Events reach the page over Server-Sent Events — the traffic is one-way, so a
WebSocket would be more machinery for nothing. Moves differ every run: the players are random, and
randomness is injected rather than reached for, so the tests are exact anyway.

## Agents as players

`A2APlayer` is the bridge, and it is deliberately trivial:

```python
def take_turn(self, view: GameView) -> PlayerTurn:
    reply = self._agent_client.send(self._context_id, view.model_dump_json())
    return PlayerTurn.model_validate_json(reply)
```

The game state goes out as JSON and the answer is parsed straight back into a validated model, so a
misbehaving agent fails at the boundary instead of corrupting a turn. Transport lives behind a
one-method `AgentClient` interface, which keeps the player pure and testable with no network.

That last part is not aspirational: `tests/integration/test_a2a_player_plays_a_game.py` runs a
remote-agent player through a real game against a scripted transport, and a second case kills the
agent mid-game to prove the other contestants play on. **What is missing is the transport itself** —
an `AgentClient` that actually speaks A2A over HTTP. Until that exists, no real agent can connect.

## Layout

```
src/agent_showdown/
  interfaces/     Protocols and frozen Pydantic models. No behaviour, no imports from modules/.
  modules/        The implementations, under the same domain names.
  cli/            Typer frontend, and the only place the container is built.
  web/            FastAPI frontend: three routes and one static page.
tests/
  fakes/          In-memory doubles for everything that touches the outside world.
  unit/           Pure classes, no IO.
  integration/    The engine end to end, the web app, plus a CLI smoke test.
```

Every module sits behind a `Protocol`, dependencies arrive through constructors, and the only code
allowed to touch the clock, the terminal, the filesystem or the random number generator is the
handful of edge modules. That is what lets the whole application — game included — run in memory:
the web tests play complete games with no socket, no sleeping and no wall clock.

The architecture is described in [`.claude/CLAUDE.md`](.claude/CLAUDE.md), and generalised as a
reusable skill in [PerArneng/agent-skills](https://github.com/PerArneng/agent-skills).

## Development

```bash
uv run pytest                  # tests
uv run mypy src tests          # types, --strict
uv run ruff check src tests    # lint
```

Python >= 3.11. Runtime deps are `typer`, `dependency-injector`, `pydantic`, `fastapi` and
`uvicorn`; everything else is development-only.
