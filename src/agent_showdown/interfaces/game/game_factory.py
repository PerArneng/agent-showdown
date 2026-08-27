from typing import Protocol

from agent_showdown.interfaces.game.board import Board
from agent_showdown.interfaces.game.game import Game


class GameFactory(Protocol):
    """Hands out a fresh game, so callers never construct one themselves."""

    def create(self, board: Board) -> Game:
        """Return a new game played on `board`."""
        ...
