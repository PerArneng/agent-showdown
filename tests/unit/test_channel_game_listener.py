from agent_showdown.interfaces.game import (
    Board,
    Direction,
    GameEndedEvent,
    GameStartedEvent,
    GameView,
    MoveBlockedEvent,
    PlayerJoinedEvent,
    PlayerMovedEvent,
    PlayerReasonedEvent,
    PlayerStats,
    PlayerStatsEvent,
    PlayerTurn,
    PlayerTurnEndedEvent,
    PlayerTurnStartedEvent,
    Position,
    RoundStartedEvent,
    TurnFailedEvent,
)
from agent_showdown.modules.game import ChannelGameListener
from tests.fakes import InMemoryEventChannel

_BOARD = Board(width=4, height=3)


class NamedPlayer:
    """The listener only ever asks a player its name."""

    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        raise NotImplementedError


def test_game_started_carries_the_board() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).game_started(_BOARD, max_rounds=10)

    assert channel.published == [GameStartedEvent(board=_BOARD, max_rounds=10)]


def test_player_joined_names_the_player() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).player_joined(NamedPlayer("alice"), Position(x=1, y=2))

    assert channel.published == [PlayerJoinedEvent(player="alice", position=Position(x=1, y=2))]


def test_round_started() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).round_started(7)

    assert channel.published == [RoundStartedEvent(round_number=7)]


def test_player_moved_carries_both_positions() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).player_moved(
        NamedPlayer("bob"), Position(x=0, y=0), Position(x=1, y=0)
    )

    assert channel.published == [
        PlayerMovedEvent(player="bob", source=Position(x=0, y=0), destination=Position(x=1, y=0))
    ]


def test_player_reasoned_carries_the_text() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).player_reasoned(NamedPlayer("bob"), "the corner is closer")

    assert channel.published == [
        PlayerReasonedEvent(player="bob", reasoning="the corner is closer")
    ]


def test_move_blocked_carries_the_direction() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).move_blocked(
        NamedPlayer("bob"), Position(x=0, y=0), Direction.LEFT
    )

    assert channel.published == [
        MoveBlockedEvent(player="bob", position=Position(x=0, y=0), direction=Direction.LEFT)
    ]


def test_turn_failed_carries_the_reason() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).turn_failed(NamedPlayer("bob"), "TimeoutError: too slow")

    assert channel.published == [TurnFailedEvent(player="bob", reason="TimeoutError: too slow")]


def test_game_ended() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).game_ended(10)

    assert channel.published == [GameEndedEvent(rounds_played=10)]


def test_player_turn_started_names_the_player() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).player_turn_started(NamedPlayer("bob"))

    assert channel.published == [PlayerTurnStartedEvent(player="bob")]


def test_player_turn_ended_carries_the_seconds() -> None:
    channel = InMemoryEventChannel()

    ChannelGameListener(channel).player_turn_ended(NamedPlayer("bob"), 12.5)

    assert channel.published == [PlayerTurnEndedEvent(player="bob", seconds=12.5)]


def test_player_stats_carries_the_running_totals() -> None:
    channel = InMemoryEventChannel()
    stats = PlayerStats(turns=3, total_seconds=12.0, average_seconds=4.0)

    ChannelGameListener(channel).player_stats(NamedPlayer("bob"), stats)

    assert channel.published == [PlayerStatsEvent(player="bob", stats=stats)]
