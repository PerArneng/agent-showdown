import asyncio
import threading
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse, StreamingResponse

from agent_showdown.interfaces.builtin_agents import AgentPlayerFactory
from agent_showdown.interfaces.config import AgentConfig
from agent_showdown.interfaces.engine import Engine
from agent_showdown.interfaces.event_channel import EventChannel, EventSubscription
from agent_showdown.interfaces.file_system import FileSystem
from agent_showdown.interfaces.game import GameSnapshot

# How long a reader waits before emitting a comment line. Keeps an idle stream alive, and bounds
# how long the loop can go without noticing the server is shutting down.
_HEARTBEAT_SECONDS = 1.0
# How long shutdown waits for the arena thread to notice. It checks between turns, so a
# slow agent mid-turn is the only thing that takes any of it.
_SHUTDOWN_SECONDS = 5.0


def create_app(
    engine: Engine,
    event_channel: EventChannel,
    file_system: FileSystem,
    agent_player_factory: AgentPlayerFactory,
    client_dir: Path,
    stopping: Callable[[], bool],
) -> FastAPI:
    """Build the web frontend. A thin adapter: it starts games and forwards events, nothing more."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # The arena is always on, so it starts with the server rather than waiting for a browser.
        # A daemon thread: uvicorn's graceful shutdown must never wait for a hundred rounds, and
        # the stop below is what ends it cleanly anyway.
        arena = threading.Thread(target=engine.run_arena, name="arena", daemon=True)
        arena.start()
        try:
            yield
        finally:
            # In `finally` because Ctrl-C cancels the lifespan *at the yield*: without it the
            # stop never runs, and a daemon thread still logging while the interpreter finalizes
            # takes the stdout lock with it — "Fatal Python error: _enter_buffered_busy".
            engine.stop_arena()
            arena.join(timeout=_SHUTDOWN_SECONDS)

    app = FastAPI(title="agent-showdown", lifespan=lifespan)

    @app.get("/")
    def index() -> HTMLResponse:
        # The client is built as a single self-contained file, so this is the whole of it.
        return HTMLResponse(file_system.read_text(client_dir / "index.html"))

    @app.post("/api/new-game", status_code=202)
    def new_game() -> Response:
        # Abandons the match in flight; the arena deals the next one on its own. Answered before
        # that happens, because the browser learns about it from the event stream like everything
        # else.
        engine.new_game()
        return Response(status_code=202)

    @app.post("/api/players", status_code=201)
    def join(config: AgentConfig) -> Response:
        # The body is the same shape `agent-showdown.yaml` uses, so a robot describes itself the
        # one way. Registering wakes a paused arena.
        engine.register_player(agent_player_factory.create(config))
        return Response(status_code=201)

    @app.delete("/api/players/{name}", status_code=204)
    def leave(name: str) -> Response:
        if not engine.unregister_player(name):
            raise HTTPException(status_code=404, detail=f"no player named {name}")
        return Response(status_code=204)

    @app.get("/api/state")
    def game_state() -> GameSnapshot:
        # The event stream has no replay, so this is how a client that connected mid-game — or
        # reconnected after one — learns the board it is drawing on.
        return engine.game_snapshot()

    @app.get("/api/events")
    async def events() -> StreamingResponse:
        return StreamingResponse(
            stream_events(event_channel.subscribe(), stopping),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


async def stream_events(
    subscription: EventSubscription, stopping: Callable[[], bool]
) -> AsyncIterator[str]:
    """One SSE connection, outliving any single game but not the server."""
    loop = asyncio.get_running_loop()
    try:
        while not stopping():
            event = await loop.run_in_executor(None, subscription.poll, _HEARTBEAT_SECONDS)
            yield ": ping\n\n" if event is None else f"data: {event.model_dump_json()}\n\n"
    finally:
        subscription.close()
