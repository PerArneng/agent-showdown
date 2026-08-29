from agent_showdown.interfaces.clock import Clock
from agent_showdown.interfaces.game import Board, Game
from agent_showdown.modules.game.default_game import DefaultGame


class DefaultGameFactory:
    """Builds a fresh `DefaultGame` per match."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def create(self, board: Board) -> Game:
        return DefaultGame(board, self._clock)
