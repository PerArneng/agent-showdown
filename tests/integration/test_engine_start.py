from collections.abc import Callable
from datetime import datetime

from agent_showdown.interfaces.game import (
    Action,
    ActionKind,
    Board,
    Direction,
    GameListener,
    PlayerTurn,
    Position,
)
from agent_showdown.modules.engine import DefaultEngine
from agent_showdown.modules.game import (
    DefaultGameFactory,
    DefaultScoreboard,
    DefaultSpellBook,
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
    actions=(Action(kind=ActionKind.MOVE, direction=Direction.UP_LEFT),),
)


_AGENT_NAMES = ("simple-strands-vllm", "simple-strands-lmstudio")


def _engine(
    console: InMemoryConsole,
    *extra_listeners: GameListener,
    snapshots: SnapshotGameListener | None = None,
    roster: ScriptedAgentRoster | None = None,
    max_games: int = 1,
    max_rounds: int = 10,
) -> DefaultEngine:
    snapshot = snapshots if snapshots is not None else SnapshotGameListener()
    logger = DefaultLogger(
        clock=FrozenClock(datetime(2025, 9, 10)),
        formatter=AnsiLogFormatter(),
        console=console,
    )
    return DefaultEngine(
        logger=logger,
        game_factory=DefaultGameFactory(
            FrozenClock(datetime(2025, 9, 10)), DefaultSpellBook(), DefaultScoreboard()
        ),
        # RIGHT, then DOWN, over and over.
        player_factory=DummyPlayerFactory(
            randomizer=FixedRandomizer([3, 1]),
            clock=FrozenClock(datetime(2025, 9, 10)),
            think_time=0.0,
        ),
        agent_roster=roster if roster is not None else ScriptedAgentRoster(
            _AGENT_NAMES, [_PLANNED]
        ),
        game_listeners=[LogGameListener(logger), *extra_listeners, snapshot],
        snapshot_source=snapshot,
        max_games=max_games,
        max_rounds=max_rounds,
    )


def test_start_plays_a_whole_game_entirely_in_memory() -> None:
    console = InMemoryConsole()

    _engine(console).start_game()

    # Players join at registration, which is why it precedes the game_started line.
    assert console.lines[:5] == [
        _INFO + "match 1 of 1 started",
        _INFO + "player dummy-1 joined at (0,0)",
        _INFO + "player simple-strands-vllm joined at (9,9)",
        _INFO + "player simple-strands-lmstudio joined at (0,9)",
        _INFO + "game started on a 10x10 board for 10 rounds",
    ]
    assert console.lines[-2] == _INFO + "game ended after 10 rounds"
    assert console.lines[-1] == _INFO + "series ended"
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


def test_a_series_plays_the_configured_number_of_matches() -> None:
    console = InMemoryConsole()

    _engine(console, max_games=3, max_rounds=2).start_game()

    assert sum("game started on" in line for line in console.lines) == 3
    assert console.lines[0] == _INFO + "match 1 of 3 started"
    assert _INFO + "match 3 of 3 started" in console.lines


def test_every_match_starts_the_robots_back_on_their_seats() -> None:
    console, recorder = InMemoryConsole(), RecordingGameListener()

    _engine(console, recorder, max_games=2, max_rounds=2).start_game()

    joins = [args for name, args in recorder.events if name == "player_joined"]
    assert joins[:3] == joins[3:]
    assert joins[0] == ("dummy-1", Position(x=0, y=0))


def test_the_tally_carries_across_the_matches_of_a_series() -> None:
    console, recorder = InMemoryConsole(), RecordingGameListener()

    _engine(console, recorder, max_games=2, max_rounds=2).start_game()

    turns = [
        args[1].turns
        for name, args in recorder.events
        if name == "player_stats" and args[0] == "dummy-1"
    ]
    # Two rounds a match, two matches, and nothing resets in between.
    assert turns == [1, 2, 3, 4]


class OnRoundStarted:
    """A listener that runs one callback, with the same reach a web shutdown hook has."""

    def __init__(self, act: Callable[[], None]) -> None:
        self._act = act

    def round_started(self, round_number: int) -> None:
        self._act()

    def __getattr__(self, name: str) -> object:
        return lambda *args, **kwargs: None


def test_a_second_start_while_one_is_running_is_refused() -> None:
    console = InMemoryConsole()
    engine = _engine(console)
    reentrant = OnRoundStarted(lambda: engine.start_game())
    engine._game_listeners = [*engine._game_listeners, reentrant]  # type: ignore[list-item]

    engine.start_game()

    assert _WARNING + "a game is already running" in console.lines


def test_stop_game_ends_the_series_where_it_stands() -> None:
    console, recorder = InMemoryConsole(), RecordingGameListener()
    engine = _engine(console, recorder, max_games=5, max_rounds=10)
    stopper = OnRoundStarted(lambda: engine.stop_game())
    engine._game_listeners = [*engine._game_listeners, stopper]  # type: ignore[list-item]

    engine.start_game()

    assert sum("game started on" in line for line in console.lines) == 1
    assert recorder.names().count("round_started") == 1
    assert console.lines[-1] == _INFO + "series ended"


def test_the_roster_is_built_once_for_the_whole_series() -> None:
    roster = ScriptedAgentRoster(_AGENT_NAMES, [_PLANNED])

    _engine(InMemoryConsole(), roster=roster, max_games=3, max_rounds=1).start_game()

    # Rebuilding it per match would mean a new model client per match, and a tally that resets.
    assert roster.rosters_created == 1
