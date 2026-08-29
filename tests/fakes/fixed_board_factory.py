from collections.abc import Sequence

from agent_showdown.interfaces.game import Board, Obstacle, Position


class FixedBoardFactory:
    """Test fake. Hands out the same board every match instead of dealing a random one.

    Defaults to a bare board, so a test that is not about terrain gets the open arena it expects.
    """

    def __init__(self, obstacles: Sequence[Obstacle] = ()) -> None:
        self._obstacles = tuple(obstacles)

    def create(self, width: int, height: int, keep_clear: Sequence[Position]) -> Board:
        return Board(width=width, height=height, obstacles=self._obstacles)
