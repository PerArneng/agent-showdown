from collections.abc import Sequence

from agent_showdown.interfaces.config import TerrainConfig
from agent_showdown.interfaces.game import (
    Board,
    Direction,
    Obstacle,
    Position,
    TerrainKind,
)
from agent_showdown.interfaces.randomizer import Randomizer
from agent_showdown.modules.game.deltas import DELTAS

# A wall never runs diagonally: it turns at right angles, like something that was built.
_ORTHOGONAL = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)
# The two ways a run may turn, by the direction it was travelling in.
_PERPENDICULAR: dict[Direction, tuple[Direction, ...]] = {
    Direction.UP: (Direction.LEFT, Direction.RIGHT),
    Direction.DOWN: (Direction.LEFT, Direction.RIGHT),
    Direction.LEFT: (Direction.UP, Direction.DOWN),
    Direction.RIGHT: (Direction.UP, Direction.DOWN),
}
# How many layouts to draw before giving up and dealing a bare board. A layout is thrown away
# when it walls a seat off from the others, which a dense config can do often but not forever.
_ATTEMPTS = 20


class RandomBoardFactory:
    """Deals a fresh layout of trees, boulders, stone walls and a well for each match.

    Pure apart from the injected randomizer: it draws squares, it does not touch the world.

    A wall is grown rather than scattered. It starts somewhere free, runs a few cells in one of
    the four orthogonal directions, and then either turns ninety degrees or leaves a doorway and
    carries straight on — so a structure reads as something built, and a robot can go round it or
    through the gap. Every layout is then checked: if a seat cannot reach the others by walking,
    the whole layout is thrown away and another is drawn.
    """

    def __init__(self, randomizer: Randomizer, config: TerrainConfig) -> None:
        self._randomizer = randomizer
        self._config = config

    def create(self, width: int, height: int, keep_clear: Sequence[Position]) -> Board:
        if not self._config.enabled:
            return Board(width=width, height=height)
        reserved = self._reserved(keep_clear)
        for _ in range(_ATTEMPTS):
            taken = self._layout(width, height, reserved)
            if self._seats_connected(width, height, keep_clear, frozenset(taken)):
                obstacles = tuple(
                    Obstacle(position=position, kind=kind) for position, kind in taken.items()
                )
                return Board(width=width, height=height, obstacles=obstacles)
        # A config dense enough to fail every attempt degrades to the board we had before
        # terrain existed, rather than looping until someone notices.
        return Board(width=width, height=height)

    def _layout(
        self, width: int, height: int, reserved: frozenset[Position]
    ) -> dict[Position, TerrainKind]:
        taken: dict[Position, TerrainKind] = {}
        for _ in range(self._count(self._config.min_walls, self._config.max_walls)):
            self._grow_wall(width, height, reserved, taken)
        self._scatter(
            TerrainKind.TREE,
            self._count(self._config.min_trees, self._config.max_trees),
            width,
            height,
            reserved,
            taken,
        )
        self._scatter(
            TerrainKind.BOULDER,
            self._count(self._config.min_boulders, self._config.max_boulders),
            width,
            height,
            reserved,
            taken,
        )
        # One well, or none. Never two: it is the landmark of the board, not scenery.
        self._scatter(
            TerrainKind.STONE_WELL, 1 if self._config.well else 0, width, height, reserved, taken
        )
        return taken

    def _grow_wall(
        self,
        width: int,
        height: int,
        reserved: frozenset[Position],
        taken: dict[Position, TerrainKind],
    ) -> None:
        """Lay one connected structure, stopping the moment it would run into something.

        A run that is cut short after a single cell is taken back again, because a lone brick in
        an open field looks like a mistake rather than a wall. That can only happen to the first
        run, or to one just past a doorway: every other run starts against the corner before it.
        """
        free = self._free(width, height, reserved, taken)
        if not free:
            return
        square = self._randomizer.choice(free)
        direction = self._randomizer.choice(_ORTHOGONAL)
        laid: list[Position] = []
        detached = True
        for segment in range(self._config.max_turns + 1):
            length = self._count(self._config.min_run, self._config.max_run)
            run: list[Position] = []
            blocked = False
            for _ in range(length):
                if not self._is_free(square, width, height, reserved, taken):
                    blocked = True
                    break
                taken[square] = TerrainKind.STONE_WALL
                run.append(square)
                square = _step(square, direction)
            if detached and len(run) == 1:
                del taken[run[0]]
                run.clear()
            laid.extend(run)
            if blocked or not run or segment == self._config.max_turns:
                return
            if self._doorway():
                # Skip one cell and carry straight on: two lengths of wall with a way through.
                square = _step(square, direction)
                detached = True
            else:
                direction = self._randomizer.choice(_PERPENDICULAR[direction])
                # Turn at the last cell laid, not at the empty one past it, so the corner joins.
                square = _step(laid[-1], direction)
                detached = False

    def _scatter(
        self,
        kind: TerrainKind,
        count: int,
        width: int,
        height: int,
        reserved: frozenset[Position],
        taken: dict[Position, TerrainKind],
    ) -> None:
        for _ in range(count):
            free = self._free(width, height, reserved, taken)
            if not free:
                return
            taken[self._randomizer.choice(free)] = kind

    def _count(self, low: int, high: int) -> int:
        low = max(0, low)
        high = max(low, high)
        return self._randomizer.choice(range(low, high + 1))

    def _doorway(self) -> bool:
        if self._config.gap_in <= 0:
            return False
        return self._randomizer.choice(range(self._config.gap_in)) == 0

    def _reserved(self, keep_clear: Sequence[Position]) -> frozenset[Position]:
        """The seats and every square touching one, so nobody is seated inside a wall."""
        return frozenset(
            Position(x=seat.x + dx, y=seat.y + dy)
            for seat in keep_clear
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
        )

    def _free(
        self,
        width: int,
        height: int,
        reserved: frozenset[Position],
        taken: dict[Position, TerrainKind],
    ) -> list[Position]:
        return [
            Position(x=x, y=y)
            for y in range(height)
            for x in range(width)
            if Position(x=x, y=y) not in reserved and Position(x=x, y=y) not in taken
        ]

    def _is_free(
        self,
        square: Position,
        width: int,
        height: int,
        reserved: frozenset[Position],
        taken: dict[Position, TerrainKind],
    ) -> bool:
        if not (0 <= square.x < width and 0 <= square.y < height):
            return False
        return square not in reserved and square not in taken

    def _seats_connected(
        self,
        width: int,
        height: int,
        keep_clear: Sequence[Position],
        blocked: frozenset[Position],
    ) -> bool:
        """Every seat must be able to walk to every other one, or the match cannot be fought.

        The flood fill steps in all eight directions, because that is how a robot moves.
        """
        if len(keep_clear) < 2:
            return True
        start = keep_clear[0]
        seen = {start}
        pending = [start]
        while pending:
            square = pending.pop()
            for direction in Direction:
                neighbour = _step(square, direction)
                if not (0 <= neighbour.x < width and 0 <= neighbour.y < height):
                    continue
                if neighbour in blocked or neighbour in seen:
                    continue
                seen.add(neighbour)
                pending.append(neighbour)
        return all(seat in seen for seat in keep_clear)


def _step(square: Position, direction: Direction) -> Position:
    dx, dy = DELTAS[direction]
    return Position(x=square.x + dx, y=square.y + dy)
