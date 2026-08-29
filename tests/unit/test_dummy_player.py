from datetime import datetime

from agent_showdown.interfaces.game import ActionKind, Board, Direction, GameView, Position
from agent_showdown.modules.game import DummyPlayer
from tests.fakes import FixedRandomizer, FrozenClock

_VIEW = GameView(
    board=Board(width=3, height=3),
    position=Position(x=1, y=1),
    round_number=1,
    health=100,
)


def _player(
    randomizer: FixedRandomizer, clock: FrozenClock, think_time: float = 0.5
) -> DummyPlayer:
    return DummyPlayer("dummy-1", randomizer, clock, think_time)


def _clock() -> FrozenClock:
    return FrozenClock(datetime(2025, 9, 10))


def test_get_name_round_trips() -> None:
    assert _player(FixedRandomizer([0]), _clock()).get_name() == "dummy-1"


def test_take_turn_returns_the_direction_the_randomizer_picked() -> None:
    directions = list(Direction)
    player = _player(FixedRandomizer([0, 3]), _clock())

    first = player.take_turn(_VIEW).actions
    second = player.take_turn(_VIEW).actions

    assert len(first) == 1 and first[0].kind is ActionKind.MOVE
    assert first[0].direction == directions[0]
    assert second[0].direction == directions[3]


def test_it_thinks_once_per_turn_for_the_configured_time() -> None:
    clock = _clock()
    player = _player(FixedRandomizer([0, 0]), clock, think_time=0.25)

    player.take_turn(_VIEW)
    player.take_turn(_VIEW)

    assert clock.slept == [0.25, 0.25]
