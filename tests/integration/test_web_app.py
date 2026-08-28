import asyncio
from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_showdown.interfaces.game import (
    Direction,
    GameEndedEvent,
    GameListener,
    GameStartedEvent,
    Move,
    Movement,
    PlayerJoinedEvent,
    PlayerTurn,
    RoundStartedEvent,
)
from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.event_channel import QueueEventChannel
from agent_showdown.modules.game import (
    ChannelGameListener,
    DefaultGameFactory,
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
    RecordingGameListener,
    ScriptedAgentRoster,
    ScriptedEventSubscription,
)

_CLIENT_DIR = Path("/app/dist")
_PAGE = "<!doctype html><title>agent-showdown</title><canvas id='board'></canvas>"
_POLL = 0.5

# The built-in agent's turn, with the model replaced by a script.
_PLANNED = PlayerTurn(
    reasoning="", movement=Movement(moves=(Move(direction=Direction.UP),))
)


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
        self.engine = self.build_engine([ChannelGameListener(self.channel)])
        self.client = TestClient(
            create_app(
                engine=self.engine,
                event_channel=self.channel,
                file_system=file_system,
                client_dir=_CLIENT_DIR,
                stopping=lambda: self.stopping,
            )
        )

    def build_engine(self, extra_listeners: Sequence[GameListener]) -> DefaultEngine:
        return DefaultEngine(
            logger=self.logger,
            game_factory=DefaultGameFactory(),
            player_factory=DummyPlayerFactory(
                randomizer=FixedRandomizer([3, 1]), clock=self.clock, think_time=0.0
            ),
            agent_roster=ScriptedAgentRoster(turns=[_PLANNED]),
            game_listeners=[LogGameListener(self.logger), *extra_listeners, self.snapshots],
            snapshot_source=self.snapshots,
        )


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


def test_start_is_accepted_and_plays_a_whole_game(app: Fixture) -> None:
    watcher = app.channel.subscribe()

    response = app.client.post("/api/start")

    assert response.status_code == 202
    events = []
    while (event := watcher.poll(_POLL)) is not None:
        events.append(event)
    # Players join at registration, so their events precede the game itself starting.
    assert [type(event).__name__ for event in events[:3]] == [
        PlayerJoinedEvent.__name__,
        PlayerJoinedEvent.__name__,
        GameStartedEvent.__name__,
    ]
    assert isinstance(events[-1], GameEndedEvent)
    assert events[-1].rounds_played == 10
    assert sum(isinstance(event, RoundStartedEvent) for event in events) == 10


def test_the_game_still_reaches_the_terminal_log(app: Fixture) -> None:
    app.client.post("/api/start")

    assert app.console.lines[0].endswith("started")
    assert app.console.lines[-1].endswith("game ended after 10 rounds")


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


def test_a_second_start_while_a_game_runs_is_refused() -> None:
    fixture = Fixture()
    watcher = RecordingGameListener()
    reentrant = ReentrantListener()
    engine = fixture.build_engine([watcher, reentrant])
    reentrant.engine = engine

    engine.start_game()

    assert reentrant.tried
    warnings = [line for line in fixture.console.lines if "WARNING" in line]
    assert warnings == ["2025-09-10 \x1b[33mWARNING\x1b[0m a game is already running"]
    # The refusal did not disturb the game already in flight.
    assert watcher.names()[-1] == "game_ended"


class ReentrantListener:
    """Starts a game from inside a game, which is exactly what the guard exists to refuse."""

    def __init__(self) -> None:
        self.engine: DefaultEngine | None = None
        self.tried = False

    def game_started(self, board: object, max_rounds: int) -> None:
        if self.engine is not None and not self.tried:
            self.tried = True
            self.engine.start_game()

    def player_joined(self, player: object, position: object) -> None: ...
    def round_started(self, round_number: int) -> None: ...
    def player_moved(self, player: object, source: object, destination: object) -> None: ...
    def player_reasoned(self, player: object, reasoning: str) -> None: ...
    def move_blocked(self, player: object, position: object, direction: object) -> None: ...
    def turn_failed(self, player: object, reason: str) -> None: ...
    def game_ended(self, rounds_played: int) -> None: ...


def test_the_state_route_answers_before_any_game(app: Fixture) -> None:
    body = app.client.get("/api/state").json()

    assert body["board"] is None
    assert body["players"] == []
    assert body["playing"] is False


def test_the_state_route_describes_the_game_that_was_played(app: Fixture) -> None:
    app.client.post("/api/start")

    body = app.client.get("/api/state").json()

    # This is what a browser that connected mid-game needs and the stream never repeats.
    assert body["board"] == {"width": 10, "height": 10}
    assert body["max_rounds"] == 10
    assert {player["name"] for player in body["players"]} == {
        "dummy-1",
        "simple-strands-1",
    }
    assert all("position" in player for player in body["players"])
