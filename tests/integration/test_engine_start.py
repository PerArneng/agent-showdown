from datetime import datetime

from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.game import DefaultGameFactory, DummyPlayerFactory, LogGameListener
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from tests.fakes import FixedRandomizer, FrozenClock, InMemoryConsole, RecordingGameListener

_INFO = "2025-09-10 \x1b[32mINFO\x1b[0m "


def _engine(console: InMemoryConsole, *extra_listeners: RecordingGameListener) -> DefaultEngine:
    logger = DefaultLogger(
        clock=FrozenClock(datetime(2025, 9, 10)),
        formatter=AnsiLogFormatter(),
        console=console,
    )
    return DefaultEngine(
        logger=logger,
        game_factory=DefaultGameFactory(),
        # RIGHT, then DOWN, over and over.
        player_factory=DummyPlayerFactory(randomizer=FixedRandomizer([3, 1])),
        game_listeners=[LogGameListener(logger), *extra_listeners],
    )


def test_start_plays_a_whole_game_entirely_in_memory() -> None:
    console = InMemoryConsole()

    _engine(console).start()

    # Players join at registration, which is why it precedes the game_started line.
    assert console.lines[:4] == [
        _INFO + "started",
        _INFO + "player dummy-1 joined at (0,0)",
        _INFO + "player dummy-2 joined at (9,9)",
        _INFO + "game started on a 10x10 board for 10 rounds",
    ]
    assert console.lines[-1] == _INFO + "game ended after 10 rounds"
    rounds = [line for line in console.lines if line.endswith(" started") and "round " in line]
    assert len(rounds) == 10
    assert rounds[0].endswith("round 1 started")
    assert rounds[-1].endswith("round 10 started")
    assert console.error_lines == []


def test_players_join_before_the_game_starts_moving_them() -> None:
    console = InMemoryConsole()

    _engine(console).start()

    first_move = next(i for i, line in enumerate(console.lines) if "moved" in line)
    last_join = max(i for i, line in enumerate(console.lines) if "joined" in line)
    assert last_join < first_move


def test_every_registered_listener_sees_the_game() -> None:
    console = InMemoryConsole()
    recorder = RecordingGameListener()

    _engine(console, recorder).start()

    assert recorder.names()[:3] == ["player_joined", "player_joined", "game_started"]
    assert recorder.names().count("round_started") == 10
    assert recorder.names()[-1] == "game_ended"
    logged_moves = sum("moved" in line for line in console.lines)
    assert logged_moves == recorder.names().count("player_moved")
