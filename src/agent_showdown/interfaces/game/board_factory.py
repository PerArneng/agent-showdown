from collections.abc import Sequence
from typing import Protocol

from agent_showdown.interfaces.game.board import Board
from agent_showdown.interfaces.game.position import Position


class BoardFactory(Protocol):
    """Deals the board a match is played on, terrain and all."""

    def create(self, width: int, height: int, keep_clear: Sequence[Position]) -> Board:
        """Return a board of `width` by `height` with no obstacle on or beside `keep_clear`.

        `keep_clear` is where robots sit down: an obstacle there, or next to there, would seat a
        contestant inside a wall.
        """
        ...
