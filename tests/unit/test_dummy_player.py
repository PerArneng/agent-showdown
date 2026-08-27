from agent_showdown.interfaces.game import Board, Direction, GameView, Position
from agent_showdown.modules.game import DummyPlayer
from tests.fakes import FixedRandomizer

_VIEW = GameView(
    board=Board(width=3, height=3),
    position=Position(x=1, y=1),
    round_number=1,
)


def test_get_name_round_trips() -> None:
    assert DummyPlayer("dummy-1", FixedRandomizer([0])).get_name() == "dummy-1"


def test_take_turn_returns_the_direction_the_randomizer_picked() -> None:
    directions = list(Direction)
    player = DummyPlayer("dummy-1", FixedRandomizer([0, 3]))

    first = player.take_turn(_VIEW).movement.moves
    second = player.take_turn(_VIEW).movement.moves

    assert first == (first[0],) and len(first) == 1
    assert first[0].direction == directions[0]
    assert second[0].direction == directions[3]
