import asyncio
import threading
import time
from collections.abc import AsyncIterator, Callable, Sequence
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_showdown.interfaces.game import (
    Action,
    ActionKind,
    ArenaPausedEvent,
    Direction,
    GameEndedEvent,
    GameListener,
    GameStartedEvent,
    PlayerJoinedEvent,
    PlayerTurn,
    RoundStartedEvent,
)
from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.event_channel import QueueEventChannel
from agent_showdown.modules.game import (
    ChannelGameListener,
    DefaultGameFactory,
    DefaultPlayerRegistry,
    DefaultScoreboard,
    DefaultSpellBook,
    DummyPlayerFactory,
    LogGameListener,
    SnapshotGameListener,
)
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from agent_showdown.web import create_app, stream_events
from tests.fakes import (
    FixedRandomizer,
    FrozenClock,
    InMemoryConsole,
    InMemoryFileSystem,
    ScriptedAgentPlayerFactory,
    ScriptedEventSubscription,
)

_CLIENT_DIR = Path("/app/dist")
_PAGE = "<!doctype html><title>agent-showdown</title><canvas id='board'></canvas>"
_POLL = 0.5

# The built-in agent's turn, with the model replaced by a script.
_PLANNED = PlayerTurn(
    reasoning="", actions=(Action(kind=ActionKind.MOVE, direction=Direction.UP),)
)


def _wait_until(condition: Callable[[], bool], seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and not condition():
        time.sleep(0.01)


def _never() -> bool:
    """A server that is not shutting down."""
    return False


def _always() -> bool:
    """A server on its way out."""
    return True


class Fixture:
    """The whole application, wired the way the container wires it, with fakes at the edges."""

    def __init__(self) -> None:
        self.console = InMemoryConsole()
        self.channel = QueueEventChannel()
        self.clock = FrozenClock(datetime(2025, 9, 10))
        self.logger = DefaultLogger(
            clock=self.clock, formatter=AnsiLogFormatter(), console=self.console
        )
        self.stopping = False
        self.snapshots = SnapshotGameListener()
        self.file_system = file_system = InMemoryFileSystem()
        file_system.write_text(_CLIENT_DIR / "index.html", _PAGE)
        self.registry = DefaultPlayerRegistry()
        self.dummies = DummyPlayerFactory(
            randomizer=FixedRandomizer([3, 1]), clock=self.clock, think_time=0.0
        )
        self.agent_factory = ScriptedAgentPlayerFactory()
        self.engine = self.build_engine([ChannelGameListener(self.channel)])
        # No `with`, so the lifespan never runs: these tests drive the arena themselves rather
        # than having a thread started under them.
        self.client = TestClient(
            create_app(
                engine=self.engine,
                event_channel=self.channel,
                file_system=file_system,
                agent_player_factory=self.agent_factory,
                client_dir=_CLIENT_DIR,
                stopping=lambda: self.stopping,
            )
        )
        self._thread = threading.Thread(target=self.engine.run_arena, daemon=True)

    def build_engine(self, extra_listeners: Sequence[GameListener]) -> DefaultEngine:
        return DefaultEngine(
            logger=self.logger,
            game_factory=DefaultGameFactory(
                FrozenClock(datetime(2025, 9, 10)), DefaultSpellBook(), DefaultScoreboard()
            ),
            game_listeners=[LogGameListener(self.logger), *extra_listeners, self.snapshots],
            snapshot_source=self.snapshots,
            player_registry=self.registry,
            max_rounds=2,
        )

    def play_until(self, condition: Callable[[], bool], seconds: float = 5.0) -> None:
        """Run the arena until the test has what it needs, then stop it."""
        self._thread.start()
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not condition():
            time.sleep(0.01)
        self.engine.stop_arena()
        self._thread.join(timeout=seconds)

    def logged(self, text: str) -> bool:
        return any(text in line for line in self.console.lines)


@pytest.fixture
def app() -> Fixture:
    return Fixture()


async def _drain(frames: AsyncIterator[str]) -> list[str]:
    """Read a stream that ends on its own."""
    return [frame async for frame in frames]


async def _take(count: int, frames: AsyncIterator[str]) -> list[str]:
    """Read `count` frames, then close the stream the way a disconnected browser would."""
    taken = []
    async for frame in frames:
        taken.append(frame)
        if len(taken) == count:
            break
    await frames.aclose()  # type: ignore[attr-defined]
    return taken


def test_the_index_is_served_from_the_file_system(app: Fixture) -> None:
    response = app.client.get("/")

    assert response.status_code == 200
    assert response.text == _PAGE
    assert "text/html" in response.headers["content-type"]


def test_new_game_is_accepted(app: Fixture) -> None:
    response = app.client.post("/api/new-game")

    # Answered before anything happens: the browser hears about the new match on the stream.
    assert response.status_code == 202
    assert app.logged("new game requested")


def test_joining_registers_a_contestant(app: Fixture) -> None:
    response = app.client.post(
        "/api/players",
        json={"name": "joiner", "base_url": "http://elsewhere/v1", "model_id": "m"},
    )

    assert response.status_code == 201
    assert [player.get_name() for player in app.registry.players()] == ["joiner"]
    # Built from the same description the config file carries.
    assert app.agent_factory.names() == ["joiner"]


def test_the_state_route_lists_who_is_in_the_arena(app: Fixture) -> None:
    app.client.post(
        "/api/players",
        json={"name": "joiner", "base_url": "http://x/v1", "model_id": "m"},
    )

    body = app.client.get("/api/state").json()

    # In the arena without being on a board: no match has seated anyone yet.
    assert body["registered"] == ["joiner"]
    assert body["players"] == []


def test_a_join_that_names_an_unknown_field_is_refused(app: Fixture) -> None:
    response = app.client.post(
        "/api/players",
        json={"name": "typo", "base_url": "http://x/v1", "model_id": "m", "max_movs": 3},
    )

    # `extra="forbid"` on the config: a typo must fail loudly rather than leave a default.
    assert response.status_code == 422
    assert app.registry.players() == ()


def test_leaving_unregisters_a_contestant(app: Fixture) -> None:
    app.client.post(
        "/api/players",
        json={"name": "quitter", "base_url": "http://x/v1", "model_id": "m"},
    )

    response = app.client.delete("/api/players/quitter")

    assert response.status_code == 204
    assert app.registry.players() == ()


def test_leaving_when_you_never_joined_is_a_404(app: Fixture) -> None:
    response = app.client.delete("/api/players/ghost")

    assert response.status_code == 404


def test_a_joined_robot_plays_without_the_browser_asking_for_a_game(app: Fixture) -> None:
    app.client.post(
        "/api/players",
        json={"name": "joiner", "base_url": "http://x/v1", "model_id": "m"},
    )
    watcher = app.channel.subscribe()

    app.play_until(lambda: app.logged("game ended after"))

    events = []
    while (event := watcher.poll(_POLL)) is not None:
        events.append(event)
    kinds = [type(event).__name__ for event in events]
    # Players join at registration, so their events precede the game itself starting.
    assert kinds[:2] == [PlayerJoinedEvent.__name__, GameStartedEvent.__name__]
    assert any(isinstance(event, GameEndedEvent) for event in events)
    assert sum(isinstance(event, RoundStartedEvent) for event in events) >= 2


def test_an_empty_arena_announces_the_pause_on_the_stream(app: Fixture) -> None:
    watcher = app.channel.subscribe()

    app.play_until(lambda: app.logged("arena paused"))

    events = []
    while (event := watcher.poll(_POLL)) is not None:
        events.append(event)
    assert [type(event).__name__ for event in events] == [ArenaPausedEvent.__name__]


def test_the_stream_turns_events_into_sse_frames() -> None:
    # Driven directly rather than over HTTP: the stream is deliberately endless, so a test client
    # reading it would wait forever for a response that never finishes.
    subscription = ScriptedEventSubscription([RoundStartedEvent(round_number=4), None])

    frames = asyncio.run(_take(2, stream_events(subscription, _never)))

    assert frames == ['data: {"type":"round_started","round_number":4}\n\n', ": ping\n\n"]


def test_the_stream_closes_its_subscription_when_the_reader_goes_away() -> None:
    subscription = ScriptedEventSubscription([RoundStartedEvent(round_number=1)])

    asyncio.run(_take(1, stream_events(subscription, _never)))

    assert subscription.closed


def test_the_stream_ends_when_the_server_is_shutting_down() -> None:
    # An endless stream would hold Ctrl-C open until uvicorn gave up and cancelled it.
    subscription = ScriptedEventSubscription([RoundStartedEvent(round_number=1)])

    frames = asyncio.run(_drain(stream_events(subscription, _always)))

    assert frames == []
    assert subscription.closed


def test_the_state_route_answers_before_any_game(app: Fixture) -> None:
    body = app.client.get("/api/state").json()

    assert body["board"] is None
    assert body["players"] == []
    assert body["registered"] == []
    assert body["playing"] is False
    assert body["paused"] is False


def test_the_state_route_says_the_arena_is_idle(app: Fixture) -> None:
    app.play_until(lambda: app.logged("arena paused"))

    body = app.client.get("/api/state").json()

    # A browser opening on an empty arena needs to say so rather than draw a dead board.
    assert body["paused"] is True


def test_the_state_route_describes_the_game_that_was_played(app: Fixture) -> None:
    app.client.post(
        "/api/players",
        json={"name": "simple-strands-1", "base_url": "http://x/v1", "model_id": "m"},
    )
    app.play_until(lambda: app.logged("game ended after"))

    body = app.client.get("/api/state").json()

    # This is what a browser that connected mid-game needs and the stream never repeats.
    assert body["board"] == {"width": 10, "height": 10}
    assert body["max_rounds"] == 2
    assert {player["name"] for player in body["players"]} == {"simple-strands-1"}
    assert all("position" in player for player in body["players"])


def test_the_arena_runs_for_the_lifetime_of_the_server(app: Fixture) -> None:
    started: list[bool] = []

    class Recorder:
        def run_arena(self) -> None:
            started.append(True)

        def stop_arena(self) -> None:
            started.append(False)

        def __getattr__(self, name: str) -> object:
            return lambda *args, **kwargs: None

    recorder = Recorder()
    client = TestClient(
        create_app(
            engine=recorder,  # type: ignore[arg-type]
            event_channel=app.channel,
            file_system=app.file_system,
            agent_player_factory=app.agent_factory,
            client_dir=_CLIENT_DIR,
            stopping=_never,
        )
    )

    # `with` is what runs the lifespan, which is where the arena thread is started and stopped.
    with client:
        _wait_until(lambda: started == [True])

    assert started == [True, False]


def test_the_arena_is_stopped_even_when_the_lifespan_is_cancelled(app: Fixture) -> None:
    stopped = threading.Event()

    class Recorder:
        def run_arena(self) -> None:
            pass

        def stop_arena(self) -> None:
            stopped.set()

        def __getattr__(self, name: str) -> object:
            return lambda *args, **kwargs: None

    api = create_app(
        engine=Recorder(),  # type: ignore[arg-type]
        event_channel=app.channel,
        file_system=app.file_system,
        agent_player_factory=app.agent_factory,
        client_dir=_CLIENT_DIR,
        stopping=_never,
    )

    async def cancel_at_the_yield() -> None:
        # Exactly what Ctrl-C does: the lifespan is cancelled where it is suspended. Without a
        # `finally` the stop never runs and a daemon thread outlives the interpreter.
        async with api.router.lifespan_context(api):
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(cancel_at_the_yield())

    assert stopped.is_set()
