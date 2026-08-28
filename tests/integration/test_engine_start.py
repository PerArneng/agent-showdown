from datetime import datetime

from agent_showdown.interfaces.game import Board, Direction, Move, Movement, PlayerTurn
from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.game import (
    DefaultGameFactory,
    DummyPlayerFactory,
    LogGameListener,
    SnapshotGameListener,
)
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from tests.fakes import (
    FixedRandomizer,
    FrozenClock,
    InMemoryConsole,
    RecordingGameListener,
    ScriptedAgentRoster,
)

_INFO = "2025-09-10 \x1b[32mINFO\x1b[0m "
_WARNING = "2025-09-10 \x1b[33mWARNING\x1b[0m "

# The built-in agent, with the model replaced by a script. No test ever reaches a model.
_PLANNED = PlayerTurn(
    reasoning="walking the diagonal",
    movement=Movement(moves=(Move(direction=Direction.UP_LEFT),)),
)


_AGENT_NAMES = ("simple-strands-vllm", "simple-strands-lmstudio")


def _engine(
    console: InMemoryConsole,
    *extra_listeners: RecordingGameListener,
    snapshots: SnapshotGameListener | None = None,
) -> DefaultEngine:
    snapshot = snapshots if snapshots is not None else SnapshotGameListener()
    logger = DefaultLogger(
        clock=FrozenClock(datetime(2025, 9, 10)),
        formatter=AnsiLogFormatter(),
        console=console,
    )
    return DefaultEngine(
        logger=logger,
        game_factory=DefaultGameFactory(),
        # RIGHT, then DOWN, over and over.
        player_factory=DummyPlayerFactory(
            randomizer=FixedRandomizer([3, 1]),
            clock=FrozenClock(datetime(2025, 9, 10)),
            think_time=0.0,
        ),
        agent_roster=ScriptedAgentRoster(_AGENT_NAMES, [_PLANNED]),
        game_listeners=[LogGameListener(logger), *extra_listeners, snapshot],
        snapshot_source=snapshot,
    )


def test_start_plays_a_whole_game_entirely_in_memory() -> None:
    console = InMemoryConsole()

    _engine(console).start_game()

    # Players join at registration, which is why it precedes the game_started line.
    assert console.lines[:5] == [
        _INFO + "started",
        _INFO + "player dummy-1 joined at (0,0)",
        _INFO + "player simple-strands-vllm joined at (9,9)",
        _INFO + "player simple-strands-lmstudio joined at (0,9)",
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

    _engine(console).start_game()

    first_move = next(i for i, line in enumerate(console.lines) if "moved" in line)
    last_join = max(i for i, line in enumerate(console.lines) if "joined" in line)
    assert last_join < first_move


def test_every_registered_listener_sees_the_game() -> None:
    console = InMemoryConsole()
    recorder = RecordingGameListener()

    _engine(console, recorder).start_game()

    assert recorder.names()[:4] == [
        "player_joined",
        "player_joined",
        "player_joined",
        "game_started",
    ]
    assert recorder.names().count("round_started") == 10
    assert recorder.names()[-1] == "game_ended"
    logged_moves = sum("moved" in line for line in console.lines)
    assert logged_moves == recorder.names().count("player_moved")


def test_the_snapshot_catches_a_late_client_up_on_the_whole_game() -> None:
    snapshots = SnapshotGameListener()

    _engine(InMemoryConsole(), snapshots=snapshots).start_game()

    snapshot = snapshots.snapshot()
    assert snapshot.board == Board(width=10, height=10)
    assert snapshot.max_rounds == 10
    assert snapshot.round_number == 10
    assert snapshot.playing is False  # the game is over, so nothing is in flight
    assert sorted(player.name for player in snapshot.players) == [
        "dummy-1",
        *sorted(_AGENT_NAMES),
    ]
