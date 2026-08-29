from datetime import datetime

from agent_showdown.interfaces.game import Board, Direction, PlayerStats, Position
from agent_showdown.modules.game import DummyPlayer, LogGameListener
from agent_showdown.modules.log import AnsiLogFormatter, DefaultLogger
from tests.fakes import FixedRandomizer, FrozenClock, InMemoryConsole

_INFO = "2025-09-10 \x1b[32mINFO\x1b[0m "
_WARNING = "2025-09-10 \x1b[33mWARNING\x1b[0m "


def _listener() -> tuple[LogGameListener, InMemoryConsole]:
    console = InMemoryConsole()
    logger = DefaultLogger(
        clock=FrozenClock(datetime(2025, 9, 10)),
        formatter=AnsiLogFormatter(),
        console=console,
    )
    return LogGameListener(logger), console


def _player() -> DummyPlayer:
    return DummyPlayer("dummy-1", FixedRandomizer([0]), FrozenClock(datetime(2025, 9, 10)), 0.0)


def test_every_event_logs_one_info_line() -> None:
    listener, console = _listener()
    player = _player()

    listener.game_started(Board(width=10, height=10), 10)
    listener.player_joined(player, Position(x=0, y=0))
    listener.round_started(3)
    listener.player_turn_started(player)
    listener.player_reasoned(player, "the corner is closer")
    listener.player_moved(player, Position(x=0, y=0), Position(x=1, y=0))
    listener.move_blocked(player, Position(x=0, y=0), Direction.UP)
    listener.player_turn_ended(player, 2.34)
    listener.player_stats(player, PlayerStats(turns=3, total_seconds=12.0, average_seconds=4.0))
    listener.game_ended(10)

    assert console.lines == [
        _INFO + "game started on a 10x10 board for 10 rounds",
        _INFO + "player dummy-1 joined at (0,0)",
        _INFO + "round 3 started",
        _INFO + "player dummy-1 started its turn",
        _INFO + "player dummy-1 reasoned: the corner is closer",
        _INFO + "player dummy-1 moved from (0,0) to (1,0)",
        _INFO + "player dummy-1 blocked moving UP from (0,0)",
        _INFO + "player dummy-1 ended its turn after 2.3s",
        _INFO
        + "player dummy-1 has taken 3 turns in 12.0s, 4.0s each,"
        + " 0 eliminations, 0 deaths, 0 wins",
        _INFO + "game ended after 10 rounds",
    ]
    assert console.error_lines == []


def test_a_failed_turn_is_a_warning_not_an_info_line() -> None:
    listener, console = _listener()

    listener.turn_failed(_player(), "AgentClientError: connection refused")

    assert console.lines == [
        _WARNING + "player dummy-1 failed its turn: AgentClientError: connection refused"
    ]
