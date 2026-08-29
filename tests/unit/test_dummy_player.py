from datetime import datetime

from agent_showdown.interfaces.game import (
    ActionKind,
    Board,
    Direction,
    GameView,
    Obstacle,
    Opponent,
    Position,
    SpellInfo,
    TerrainKind,
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


def _seeing_across(*opponents: Opponent) -> GameView:
    """The same, on a board with room to walk: from (2,2) not everything is already adjacent."""
    return _VIEW.model_copy(
        update={
            "board": Board(width=5, height=5),
            "position": Position(x=2, y=2),
            "opponents": opponents,
            "spells": (_FIREBALL,),
        }
    )


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
    # From (2,2) towards (0,4): one step LEFT and DOWN at once.
    target = Opponent(name="rusty", position=Position(x=0, y=4), health=100, distance=2)

    actions = player.take_turn(_seeing_across(target)).actions

    assert actions[0].kind is ActionKind.MOVE
    assert actions[0].direction is Direction.DOWN_LEFT


def test_it_sidesteps_rather_than_walking_onto_the_robot_it_is_chasing() -> None:
    """The diagonal would land on the target's square, which is barred, so it goes round."""
    player = _player(FixedRandomizer([0]), _clock())
    # Adjacent and not lined up, so there is no shot to take and nowhere straight to go.
    target = Opponent(name="rusty", position=Position(x=0, y=2), health=100, distance=1)

    actions = player.take_turn(_seeing(target)).actions

    assert actions[0].kind is ActionKind.MOVE
    assert actions[0].direction is Direction.LEFT


def test_it_walks_towards_the_nearest_of_several() -> None:
    player = _player(FixedRandomizer([0]), _clock())
    near = Opponent(name="near", position=Position(x=2, y=0), health=100, distance=2)
    far = Opponent(name="far", position=Position(x=4, y=4), health=100, distance=4)

    # `near` is lined up, so the shot would win; drop its direction to leave only the walk.
    plain = near.model_copy(update={"direction": None})
    actions = player.take_turn(_seeing_across(far, plain)).actions

    assert actions[0].direction is Direction.UP  # towards `near` at (2,0) from (2,2)


def test_a_scrapped_robot_is_neither_shot_at_nor_chased() -> None:
    player = _player(FixedRandomizer([0]), _clock())
    corpse = Opponent(
        name="dead", position=Position(x=1, y=0), health=0, direction=Direction.UP, distance=1
    )

    actions = player.take_turn(_seeing(corpse)).actions

    # Nobody left to fight, so it falls back to wandering on the randomizer — over the open
    # squares only, which is why UP, the first direction of all, is not the one it draws.
    assert actions[0].kind is ActionKind.MOVE
    assert actions[0].direction is Direction.DOWN


def test_an_empty_arena_still_makes_it_wander() -> None:
    player = _player(FixedRandomizer([3]), _clock())

    actions = player.take_turn(_seeing()).actions

    assert actions[0].kind is ActionKind.MOVE
    assert actions[0].direction == list(Direction)[3]


def _board(*squares: Position) -> Board:
    return Board(
        width=3,
        height=3,
        obstacles=tuple(
            Obstacle(position=square, kind=TerrainKind.BOULDER) for square in squares
        ),
    )


def test_it_sidesteps_a_boulder_standing_on_the_way_to_its_target() -> None:
    """The diagonal is blocked, so it takes the axis step that still closes the gap."""
    view = _VIEW.model_copy(
        update={
            "board": _board(Position(x=2, y=2)),
            "position": Position(x=1, y=1),
            "opponents": (
                Opponent(name="rusty", position=Position(x=2, y=2), health=100, distance=1),
            ),
        }
    )

    actions = _player(FixedRandomizer([0]), _clock()).take_turn(view).actions

    assert actions[0].direction == Direction.RIGHT


def test_it_wanders_onto_open_ground_rather_than_into_terrain() -> None:
    """Boxed in on every side but one, the only step it can draw is the one that is open."""
    walls = tuple(
        Position(x=x, y=y)
        for x in range(3)
        for y in range(3)
        if (x, y) not in {(1, 1), (2, 2)}
    )
    view = _VIEW.model_copy(update={"board": _board(*walls)})

    for index in range(8):
        action = _player(FixedRandomizer([index]), _clock()).take_turn(view).actions[0]
        assert action.direction == Direction.DOWN_RIGHT
