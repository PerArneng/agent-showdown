from agent_showdown.interfaces.game import (
    Board,
    Direction,
    GameListener,
    GameView,
    PlayerTurn,
    Position,
)
from agent_showdown.modules.game import SnapshotGameListener

_BOARD = Board(width=4, height=3)


class _NamedPlayer:
    """The listener only ever asks a player its name."""

    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name

    def take_turn(self, view: GameView) -> PlayerTurn:
        raise NotImplementedError


def test_nothing_has_happened_yet() -> None:
    snapshot = SnapshotGameListener().snapshot()

    assert snapshot.board is None
    assert snapshot.players == ()
    assert snapshot.playing is False


def test_the_board_arrives_with_the_game() -> None:
    listener = SnapshotGameListener()

    listener.game_started(_BOARD, max_rounds=7)

    assert listener.snapshot().board == _BOARD
    assert listener.snapshot().max_rounds == 7


def test_a_player_is_remembered_where_it_joined() -> None:
    listener = SnapshotGameListener()
    listener.game_started(_BOARD, max_rounds=7)

    listener.player_joined(_NamedPlayer("a"), Position(x=1, y=2))

    assert listener.snapshot().players[0].name == "a"
    assert listener.snapshot().players[0].position == Position(x=1, y=2)


def test_a_move_replaces_the_position_rather_than_adding_a_player() -> None:
    listener = SnapshotGameListener()
    player = _NamedPlayer("a")
    listener.player_joined(player, Position(x=1, y=2))

    listener.player_moved(player, Position(x=1, y=2), Position(x=3, y=0))

    assert len(listener.snapshot().players) == 1
    assert listener.snapshot().players[0].position == Position(x=3, y=0)


def test_reasoning_is_kept_so_a_late_client_sees_the_last_plan() -> None:
    listener = SnapshotGameListener()
    player = _NamedPlayer("a")
    listener.player_joined(player, Position(x=1, y=2))

    listener.player_reasoned(player, "heading for the middle")

    assert listener.snapshot().players[0].reasoning == "heading for the middle"
    assert listener.snapshot().players[0].position == Position(x=1, y=2)


def test_a_move_keeps_the_reasoning_it_was_planned_with() -> None:
    listener = SnapshotGameListener()
    player = _NamedPlayer("a")
    listener.player_joined(player, Position(x=1, y=2))
    listener.player_reasoned(player, "heading for the middle")

    listener.player_moved(player, Position(x=1, y=2), Position(x=2, y=2))

    assert listener.snapshot().players[0].reasoning == "heading for the middle"


def test_rounds_mark_the_game_as_playing_and_the_end_stops_it() -> None:
    listener = SnapshotGameListener()
    listener.game_started(_BOARD, max_rounds=7)

    listener.round_started(3)
    assert (listener.snapshot().round_number, listener.snapshot().playing) == (3, True)

    listener.game_ended(rounds_played=7)
    assert listener.snapshot().playing is False
    assert listener.snapshot().round_number == 3  # the last round still stands


def test_a_new_game_does_not_inherit_the_last_ones_players() -> None:
    listener = SnapshotGameListener()
    listener.game_started(_BOARD, max_rounds=7)
    listener.player_joined(_NamedPlayer("a"), Position(x=1, y=2))

    listener.game_started(Board(width=9, height=9), max_rounds=2)

    assert listener.snapshot().players == ()
    assert listener.snapshot().board == Board(width=9, height=9)


def test_a_blocked_move_and_a_failed_turn_leave_the_snapshot_alone() -> None:
    listener = SnapshotGameListener()
    player = _NamedPlayer("a")
    listener.player_joined(player, Position(x=1, y=2))
    before = listener.snapshot()

    listener.move_blocked(player, Position(x=1, y=2), Direction.UP)
    listener.turn_failed(player, "the model is unreachable")

    assert listener.snapshot() == before


def test_the_snapshot_is_replaced_never_mutated() -> None:
    # This is what lets HTTP threads read it without a lock.
    listener = SnapshotGameListener()
    listener.game_started(_BOARD, max_rounds=7)
    before = listener.snapshot()

    listener.round_started(1)

    assert listener.snapshot() is not before
    assert before.round_number == 0

def test_it_is_a_game_listener() -> None:
    # Structural, so mypy enforces it: registering it must not need the game to know the class.
    listener: GameListener = SnapshotGameListener()

    assert listener is not None
