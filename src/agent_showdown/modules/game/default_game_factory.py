from agent_showdown.interfaces.game import Board, Game
from agent_showdown.modules.game.default_game import DefaultGame


class DefaultGameFactory:
    """Builds a fresh `DefaultGame` per match."""

    def create(self, board: Board) -> Game:
        return DefaultGame(board)
