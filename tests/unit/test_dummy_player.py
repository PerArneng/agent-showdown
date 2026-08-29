from datetime import datetime

from agent_showdown.interfaces.game import (
    ActionKind,
    Board,
    Direction,
    GameView,
    Opponent,
    Position,
    SpellInfo,
)
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


_FIREBALL = SpellInfo(name="fireball", description="A bolt.", damage=10, range=3)


def _seeing(*opponents: Opponent) -> GameView:
    return _VIEW.model_copy(update={"opponents": opponents, "spells": (_FIREBALL,)})


def test_it_takes_the_shot_when_one_is_lined_up() -> None:
    player = _player(FixedRandomizer([0]), _clock())
    target = Opponent(
        name="rusty", position=Position(x=1, y=0), health=100, direction=Direction.UP, distance=1
    )

    actions = player.take_turn(_seeing(target)).actions

    assert len(actions) == 1
    assert actions[0].kind is ActionKind.CAST
    assert actions[0].spell == "fireball"
    assert actions[0].direction is Direction.UP


def test_a_robot_out_of_range_is_walked_towards_rather_than_shot_at() -> None:
    player = _player(FixedRandomizer([0]), _clock())
    far = Opponent(
        name="rusty", position=Position(x=1, y=9), health=100, direction=Direction.DOWN, distance=8
    )

    actions = player.take_turn(_seeing(far)).actions

    assert actions[0].kind is ActionKind.MOVE
    assert actions[0].direction is Direction.DOWN


def test_it_closes_diagonally_when_both_axes_are_apart() -> None:
    player = _player(FixedRandomizer([0]), _clock())
    # From (1,1) towards (0,2): one step LEFT and DOWN at once.
    target = Opponent(name="rusty", position=Position(x=0, y=2), health=100, distance=1)

    actions = player.take_turn(_seeing(target)).actions

    assert actions[0].kind is ActionKind.MOVE
    assert actions[0].direction is Direction.DOWN_LEFT


def test_it_walks_towards_the_nearest_of_several() -> None:
    player = _player(FixedRandomizer([0]), _clock())
    near = Opponent(name="near", position=Position(x=1, y=0), health=100, distance=1)
    far = Opponent(name="far", position=Position(x=2, y=2), health=100, distance=4)

    # `near` is lined up but the view says it is 1 away, so the shot wins; drop its direction.
    plain = near.model_copy(update={"direction": None})
    actions = player.take_turn(_seeing(far, plain)).actions

    assert actions[0].direction is Direction.UP  # towards `near` at (1,0) from (1,1)


def test_a_scrapped_robot_is_neither_shot_at_nor_chased() -> None:
    player = _player(FixedRandomizer([0]), _clock())
    corpse = Opponent(
        name="dead", position=Position(x=1, y=0), health=0, direction=Direction.UP, distance=1
    )

    actions = player.take_turn(_seeing(corpse)).actions

    # Nobody left to fight, so it falls back to wandering on the randomizer.
    assert actions[0].kind is ActionKind.MOVE
    assert actions[0].direction == list(Direction)[0]


def test_an_empty_arena_still_makes_it_wander() -> None:
    player = _player(FixedRandomizer([3]), _clock())

    actions = player.take_turn(_seeing()).actions

    assert actions[0].kind is ActionKind.MOVE
    assert actions[0].direction == list(Direction)[3]
