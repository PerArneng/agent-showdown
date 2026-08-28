import asyncio
from collections.abc import AsyncIterator, Callable
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Response
from fastapi.responses import HTMLResponse, StreamingResponse

from agent_showdown.interfaces.engine import Engine
from agent_showdown.interfaces.event_channel import EventChannel, EventSubscription
from agent_showdown.interfaces.file_system import FileSystem
from agent_showdown.interfaces.game import GameSnapshot

# How long a reader waits before emitting a comment line. Keeps an idle stream alive, and bounds
# how long the loop can go without noticing the server is shutting down.
_HEARTBEAT_SECONDS = 1.0


def create_app(
    engine: Engine,
    event_channel: EventChannel,
    file_system: FileSystem,
    client_dir: Path,
    stopping: Callable[[], bool],
) -> FastAPI:
    """Build the web frontend. A thin adapter: it starts games and forwards events, nothing more."""
    app = FastAPI(title="agent-showdown")

    @app.get("/")
    def index() -> HTMLResponse:
        # The client is built as a single self-contained file, so this is the whole of it.
        return HTMLResponse(file_system.read_text(client_dir / "index.html"))

    @app.post("/api/start", status_code=202)
    def start_game(background_tasks: BackgroundTasks) -> Response:
        # Runs after the response is sent, so the browser is already listening when the game
        # begins. The engine refuses a second concurrent game itself.
        background_tasks.add_task(engine.start_game)
        return Response(status_code=202)

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
