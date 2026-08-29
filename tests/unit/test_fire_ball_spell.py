from agent_showdown.interfaces.game import Board, Direction, Position
from agent_showdown.modules.game import FireBallSpell

_BOARD = Board(width=6, height=6)


def _cast(
    origin: Position, direction: Direction, *occupied: Position, board: Board = _BOARD
) -> tuple[tuple[Position, ...], Position | None]:
    effect = FireBallSpell().cast(origin, direction, board, frozenset(occupied))
    return effect.path, effect.impact


def test_it_describes_itself_by_the_name_an_action_must_use() -> None:
    spell = FireBallSpell().describe()

    assert spell.name == "fireball"
    assert (spell.damage, spell.range) == (10, 3)


def test_an_empty_lane_is_travelled_to_the_full_range() -> None:
    path, impact = _cast(Position(x=0, y=0), Direction.RIGHT)

    assert path == (Position(x=1, y=0), Position(x=2, y=0), Position(x=3, y=0))
    assert impact is None


def test_it_stops_on_the_first_occupied_square() -> None:
    path, impact = _cast(
        Position(x=0, y=0), Direction.RIGHT, Position(x=2, y=0), Position(x=3, y=0)
    )

    assert path == (Position(x=1, y=0), Position(x=2, y=0))
    assert impact == Position(x=2, y=0)


def test_a_robot_one_square_further_than_the_range_is_out_of_reach() -> None:
    path, impact = _cast(Position(x=0, y=0), Direction.RIGHT, Position(x=4, y=0))

    assert impact is None
    assert Position(x=4, y=0) not in path


def test_it_fizzles_at_the_wall_rather_than_flying_off_the_board() -> None:
    path, impact = _cast(Position(x=4, y=0), Direction.RIGHT)

    assert path == (Position(x=5, y=0),)
    assert impact is None


def test_a_robot_with_its_back_to_the_wall_throws_nothing() -> None:
    path, impact = _cast(Position(x=0, y=0), Direction.LEFT)

    assert path == ()
    assert impact is None


def test_a_diagonal_travels_both_axes_and_up_decreases_y() -> None:
    path, _ = _cast(Position(x=0, y=3), Direction.UP_RIGHT)

    assert path == (Position(x=1, y=2), Position(x=2, y=1), Position(x=3, y=0))


def test_it_never_reports_the_square_it_was_cast_from() -> None:
    path, impact = _cast(Position(x=2, y=2), Direction.UP, Position(x=2, y=2))

    assert Position(x=2, y=2) not in path
    assert impact != Position(x=2, y=2)
