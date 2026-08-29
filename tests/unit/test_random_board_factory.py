from agent_showdown.interfaces.config import TerrainConfig
from agent_showdown.interfaces.game import Board, Direction, Position, TerrainKind
from agent_showdown.modules.game import RandomBoardFactory
from agent_showdown.modules.game.deltas import DELTAS
from agent_showdown.modules.randomizer import SystemRandomizer
from tests.fakes import FixedRandomizer

_SEATS = (
    Position(x=0, y=0),
    Position(x=9, y=9),
    Position(x=0, y=9),
    Position(x=9, y=0),
)


def _boards(config: TerrainConfig, count: int = 30) -> list[Board]:
    """A sweep of layouts. Seeded, so the entropy is real but the test is not flaky."""
    return [
        RandomBoardFactory(SystemRandomizer(seed=seed), config).create(10, 10, _SEATS)
        for seed in range(count)
    ]


def _blocked(board: Board) -> set[Position]:
    return {obstacle.position for obstacle in board.obstacles}


def _reachable(board: Board) -> set[Position]:
    blocked = _blocked(board)
    seen = {_SEATS[0]}
    pending = [_SEATS[0]]
    while pending:
        square = pending.pop()
        for direction in Direction:
            dx, dy = DELTAS[direction]
            neighbour = Position(x=square.x + dx, y=square.y + dy)
            if not (0 <= neighbour.x < board.width and 0 <= neighbour.y < board.height):
                continue
            if neighbour in blocked or neighbour in seen:
                continue
            seen.add(neighbour)
            pending.append(neighbour)
    return seen


def test_terrain_switched_off_deals_the_bare_board_the_arena_had_before() -> None:
    factory = RandomBoardFactory(FixedRandomizer([0]), TerrainConfig(enabled=False))

    board = factory.create(10, 10, _SEATS)

    assert board == Board(width=10, height=10)


def test_every_obstacle_lands_on_the_board_and_on_a_square_of_its_own() -> None:
    for board in _boards(TerrainConfig()):
        squares = [obstacle.position for obstacle in board.obstacles]
        assert len(squares) == len(set(squares))
        assert all(0 <= square.x < 10 and 0 <= square.y < 10 for square in squares)


def test_no_obstacle_stands_on_a_seat_or_beside_one() -> None:
    for board in _boards(TerrainConfig()):
        for square in _blocked(board):
            for seat in _SEATS:
                assert max(abs(square.x - seat.x), abs(square.y - seat.y)) > 1


def test_every_seat_can_walk_to_every_other_one() -> None:
    for board in _boards(TerrainConfig()):
        reachable = _reachable(board)
        assert all(seat in reachable for seat in _SEATS)


def test_a_wall_cell_always_touches_another_one_edge_on() -> None:
    """A run is at least two cells and never turns diagonally, so no wall cell stands alone."""
    orthogonal = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)
    for board in _boards(TerrainConfig(min_trees=0, max_trees=0, min_boulders=0, max_boulders=0)):
        walls = {
            obstacle.position
            for obstacle in board.obstacles
            if obstacle.kind == TerrainKind.STONE_WALL
        }
        for square in walls:
            neighbours = [
                Position(x=square.x + DELTAS[direction][0], y=square.y + DELTAS[direction][1])
                for direction in orthogonal
            ]
            assert any(neighbour in walls for neighbour in neighbours)


def test_the_kinds_asked_for_are_the_kinds_dealt() -> None:
    config = TerrainConfig(min_walls=1, max_walls=1, min_trees=1, max_trees=1, min_boulders=1,
                           max_boulders=1)
    kinds = {obstacle.kind for board in _boards(config) for obstacle in board.obstacles}

    assert kinds == {
        TerrainKind.STONE_WALL,
        TerrainKind.TREE,
        TerrainKind.BOULDER,
        TerrainKind.STONE_WELL,
    }


def _wells(board: Board) -> int:
    return sum(1 for obstacle in board.obstacles if obstacle.kind == TerrainKind.STONE_WELL)


def test_a_board_is_never_dealt_a_second_well() -> None:
    """The well is the landmark of the arena, so there is one of it or there is none."""
    assert {_wells(board) for board in _boards(TerrainConfig())} == {1}


def test_the_well_can_be_left_out_without_taking_the_rest_of_the_terrain_with_it() -> None:
    boards = _boards(TerrainConfig(well=False))

    assert all(_wells(board) == 0 for board in boards)
    assert all(board.obstacles for board in boards)


def test_the_well_blocks_its_square_like_any_other_terrain() -> None:
    """It is scenery to look at and a rule to play around, the same as a boulder."""
    for board in _boards(TerrainConfig()):
        well = next(o for o in board.obstacles if o.kind == TerrainKind.STONE_WELL)
        assert well.position not in _reachable(board)


def test_a_config_dense_enough_to_seal_the_arena_still_deals_a_playable_board() -> None:
    """Every attempt walls a seat in, so the generator gives up and hands back a bare board."""
    seats = (Position(x=0, y=0), Position(x=5, y=5))
    factory = RandomBoardFactory(
        SystemRandomizer(seed=0),
        TerrainConfig(min_walls=40, max_walls=40, min_run=8, max_run=8, gap_in=0),
    )

    board = factory.create(6, 6, seats)

    assert board.obstacles == ()


def test_an_arena_with_no_room_left_deals_nothing_rather_than_looping() -> None:
    """Four seats on a 3x3 board reserve every square, so there is nowhere to put anything."""
    factory = RandomBoardFactory(SystemRandomizer(seed=0), TerrainConfig())

    board = factory.create(3, 3, _SEATS)

    assert board == Board(width=3, height=3)
